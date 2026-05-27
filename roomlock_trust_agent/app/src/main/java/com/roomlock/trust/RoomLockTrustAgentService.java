package com.roomlock.trust;

import android.net.wifi.ScanResult;
import android.service.trust.TrustAgentService;
import android.util.Log;

import com.roomlock.trust.roomlock.RoomLockAuthenticator;
import com.roomlock.trust.roomlock.RoomLockProfile;
import com.roomlock.trust.roomlock.RoomLockStore;
import com.roomlock.trust.roomlock.RoomLockWifiScanner;

import java.util.List;

public final class RoomLockTrustAgentService extends TrustAgentService {
    private static final String TAG = "RoomLockTrustAgent";
    private static final long TRUST_DURATION_MS = 2 * 60 * 1000L;
    private static final int AUTH_SCAN_COUNT = 4;
    private static final long AUTH_SCAN_DELAY_MS = 1000L;

    private boolean authenticating;

    @Override
    public void onCreate() {
        super.onCreate();
        setManagingTrust(true);
        authenticateThenGrant(false);
    }

    @Override
    public void onDeviceLocked() {
        authenticateThenGrant(false);
    }

    @Override
    public void onUserMayRequestUnlock() {
        authenticateThenGrant(false);
    }

    @Override
    public void onUserRequestedUnlock(boolean dismissKeyguard) {
        authenticateThenGrant(dismissKeyguard);
    }

    private void authenticateThenGrant(boolean dismissKeyguard) {
        if (authenticating) {
            Log.i(TAG, "Authentication already running");
            return;
        }

        RoomLockProfile profile = new RoomLockStore(this).load();
        if (profile == null) {
            Log.i(TAG, "No RoomLock profile; revoking trust");
            revokeTrust();
            return;
        }

        Log.i(TAG, "Starting RoomLock authentication");
        authenticating = true;
        new RoomLockWifiScanner(this).collect(AUTH_SCAN_COUNT, new RoomLockWifiScanner.Callback() {
            @Override
            public void onProgress(int done, int total) {
                Log.i(TAG, "Wi-Fi auth scan " + done + "/" + total);
            }

            @Override
            public void onComplete(List<List<ScanResult>> samples) {
                authenticating = false;
                boolean ok = new RoomLockAuthenticator(RoomLockTrustAgentService.this)
                        .authenticate(profile, samples);
                if (ok) {
                    Log.i(TAG, "RoomLock authentication passed; granting trust");
                    int flags = FLAG_GRANT_TRUST_TEMPORARY_AND_RENEWABLE;
                    if (dismissKeyguard) {
                        flags |= FLAG_GRANT_TRUST_DISMISS_KEYGUARD;
                    }
                    grantTrust(getString(R.string.trust_message), TRUST_DURATION_MS, flags);
                } else {
                    Log.i(TAG, "RoomLock authentication failed; revoking trust");
                    revokeTrust();
                }
            }

            @Override
            public void onError(String message) {
                authenticating = false;
                Log.i(TAG, "RoomLock scan failed: " + message);
                revokeTrust();
            }
        }, AUTH_SCAN_DELAY_MS);
    }
}
