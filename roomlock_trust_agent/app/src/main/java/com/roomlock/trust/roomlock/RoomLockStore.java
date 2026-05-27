package com.roomlock.trust.roomlock;

import android.content.Context;
import android.content.SharedPreferences;

import org.json.JSONException;

public final class RoomLockStore {
    private static final String PREFS = "roomlock";
    private static final String KEY_PROFILE = "profile";

    private final SharedPreferences prefs;

    public RoomLockStore(Context context) {
        Context storageContext = context.createDeviceProtectedStorageContext();
        prefs = storageContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public boolean hasProfile() {
        return prefs.contains(KEY_PROFILE);
    }

    public RoomLockProfile load() {
        String json = prefs.getString(KEY_PROFILE, null);
        if (json == null) {
            return null;
        }
        try {
            return RoomLockProfile.fromJson(json);
        } catch (JSONException e) {
            return null;
        }
    }

    public void save(RoomLockProfile profile) {
        try {
            prefs.edit().putString(KEY_PROFILE, profile.toJson().toString()).apply();
        } catch (JSONException e) {
            throw new IllegalStateException("Could not save RoomLock profile", e);
        }
    }
}
