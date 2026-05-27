package com.roomlock.trust.roomlock;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public final class RoomLockProfile {
    public final double[] dist;
    public final double[] rad;
    public final double[] base;
    public final String passwordHash;

    public RoomLockProfile(double[] dist, double[] rad, double[] base, String passwordHash) {
        this.dist = dist;
        this.rad = rad;
        this.base = base;
        this.passwordHash = passwordHash;
    }

    JSONObject toJson() throws JSONException {
        JSONObject object = new JSONObject();
        object.put("dist", toJsonArray(dist));
        object.put("rad", toJsonArray(rad));
        object.put("base", toJsonArray(base));
        object.put("passwordHash", passwordHash);
        return object;
    }

    static RoomLockProfile fromJson(String json) throws JSONException {
        JSONObject object = new JSONObject(json);
        return new RoomLockProfile(
                fromJsonArray(object.getJSONArray("dist")),
                fromJsonArray(object.getJSONArray("rad")),
                fromJsonArray(object.getJSONArray("base")),
                object.getString("passwordHash"));
    }

    private static JSONArray toJsonArray(double[] values) throws JSONException {
        JSONArray array = new JSONArray();
        for (double value : values) {
            array.put(value);
        }
        return array;
    }

    private static double[] fromJsonArray(JSONArray array) throws JSONException {
        double[] values = new double[array.length()];
        for (int i = 0; i < values.length; i++) {
            values[i] = array.getDouble(i);
        }
        return values;
    }
}
