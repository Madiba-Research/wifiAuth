package com.roomlock.trust;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.wifi.ScanResult;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.roomlock.trust.roomlock.RoomLockAuthenticator;
import com.roomlock.trust.roomlock.RoomLockProfile;
import com.roomlock.trust.roomlock.RoomLockStore;
import com.roomlock.trust.roomlock.RoomLockWifiScanner;

import java.util.ArrayList;
import java.util.List;

public final class RoomLockSettingsActivity extends Activity {
    private static final int REQUEST_PERMISSIONS = 1;
    private static final int REGISTER_SCAN_COUNT = 40;

    private static final long REGISTER_SCAN_DELAY_MS = 1500L;


    private TextView statusView;
    private Button registerButton;
    private RoomLockStore store;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        store = new RoomLockStore(this);
        startKeepAliveService();

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER_VERTICAL);
        layout.setPadding(48, 48, 48, 48);

        statusView = new TextView(this);
        statusView.setText(store.hasProfile() ? R.string.registered : R.string.not_registered);

        registerButton = new Button(this);
        registerButton.setText(R.string.register);
        registerButton.setOnClickListener(view -> startRegistration());

        layout.addView(statusView);
        layout.addView(registerButton);
        setContentView(layout);
    }

    private void startRegistration() {
        if (!hasRequiredPermissions()) {
            requestPermissions(requiredPermissions(), REQUEST_PERMISSIONS);
            statusView.setText(R.string.missing_permission);
            return;
        }

        registerButton.setEnabled(false);
        RoomLockWifiScanner scanner = new RoomLockWifiScanner(this);
        scanner.collect(REGISTER_SCAN_COUNT, new RoomLockWifiScanner.Callback() {
            @Override
            public void onProgress(int done, int total) {
                statusView.setText("Registering " + done + "/" + total);
            }

            @Override
            public void onComplete(List<List<ScanResult>> samples) {
                RoomLockProfile profile = new RoomLockAuthenticator(RoomLockSettingsActivity.this)
                        .register(samples);
                store.save(profile);
                startKeepAliveService();
                statusView.setText(R.string.registered);
                registerButton.setEnabled(true);
            }

            @Override
            public void onError(String message) {
                statusView.setText(message);
                registerButton.setEnabled(true);
            }
        }, REGISTER_SCAN_DELAY_MS);
    }

    private boolean hasRequiredPermissions() {
        for (String permission : requiredPermissions()) {
            if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
                return false;
            }
        }
        return true;
    }

    private String[] requiredPermissions() {
        List<String> permissions = new ArrayList<>();
        permissions.add(Manifest.permission.ACCESS_FINE_LOCATION);
        if (Build.VERSION.SDK_INT >= 33) {
            permissions.add(Manifest.permission.NEARBY_WIFI_DEVICES);
        }
        return permissions.toArray(new String[0]);
    }

    private void startKeepAliveService() {
        Intent intent = new Intent(this, RoomLockKeepAliveService.class);
        if (Build.VERSION.SDK_INT >= 26) {
            startForegroundService(intent);
        } else {
            startService(intent);
        }
    }
}
