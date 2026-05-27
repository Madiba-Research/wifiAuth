package android.service.trust;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

public class TrustAgentService extends Service {
    public static final String SERVICE_INTERFACE = "android.service.trust.TrustAgentService";
    public static final String TRUST_AGENT_META_DATA = "android.service.trust.trustagent";
    public static final int FLAG_GRANT_TRUST_DISMISS_KEYGUARD = 1 << 1;
    public static final int FLAG_GRANT_TRUST_TEMPORARY_AND_RENEWABLE = 1 << 2;

    public final void grantTrust(CharSequence message, long durationMs, int flags) {
    }

    public void onDeviceLocked() {
    }

    public void onUserMayRequestUnlock() {
    }

    public void onUserRequestedUnlock(boolean dismissKeyguard) {
    }

    public final void revokeTrust() {
    }

    public final void setManagingTrust(boolean managingTrust) {
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
