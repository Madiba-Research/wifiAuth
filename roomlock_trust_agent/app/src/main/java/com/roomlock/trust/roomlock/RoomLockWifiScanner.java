package com.roomlock.trust.roomlock;

import android.content.Context;
import android.net.wifi.ScanResult;
import android.net.wifi.WifiManager;
import android.os.Handler;
import android.os.Looper;

import java.util.ArrayList;
import java.util.List;

public final class RoomLockWifiScanner {
//    private static final long AUTH_SCAN_DELAY_MS = 1000L;

//    private static final long REGISTER_SCAN_DELAY_MS = 1500L;


    public interface Callback {
        void onProgress(int done, int total);

        void onComplete(List<List<ScanResult>> samples);

        void onError(String message);
    }

    private final WifiManager wifiManager;
    private final Handler handler = new Handler(Looper.getMainLooper());

    public RoomLockWifiScanner(Context context) {
        wifiManager = (WifiManager) context.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
    }

    public void collect(int count, Callback callback, long scanDelayMs) {
        if (wifiManager == null) {
            callback.onError("Wi-Fi service is unavailable.");
            return;
        }
        collectNext(count, new ArrayList<>(), callback, scanDelayMs);
    }

    private void collectNext(int count, List<List<ScanResult>> samples, Callback callback, long scanDelayMs) {
        if (samples.size() >= count) {
            callback.onComplete(samples);
            return;
        }

        try {
            wifiManager.startScan();
        } catch (SecurityException e) {
            callback.onError("Missing Wi-Fi/location permission.");
            return;
        }

        handler.postDelayed(() -> {
            try {
                List<ScanResult> results = wifiManager.getScanResults();
                if (results == null || results.isEmpty()) {
                    callback.onError("No Wi-Fi scan results.");
                    return;
                }
                samples.add(new ArrayList<>(results));
                callback.onProgress(samples.size(), count);
                collectNext(count, samples, callback, scanDelayMs);
            } catch (SecurityException e) {
                callback.onError("Missing Wi-Fi/location permission.");
            }
        }, scanDelayMs);
    }
}
