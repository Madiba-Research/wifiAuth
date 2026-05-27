package com.roomlock.trust.roomlock;

import android.content.Context;
import android.net.wifi.ScanResult;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.util.List;

public final class RoomLockAuthenticator {
//    private static final double SIGMA = 1.3;
    private static final double SIGMA = 2.0;

    private final double[][] h;
    private final double[][] g;
    private final RoomLockEncoder encoder;

    public RoomLockAuthenticator(Context context) {
        try {
            JSONObject matrices = new JSONObject(readAsset(context, "roomlock_matrices.json"));
            h = readMatrix(matrices.getJSONArray("H"));
            g = readMatrix(matrices.getJSONArray("G"));
            encoder = new RoomLockEncoder(context);
        } catch (Exception e) {
            throw new IllegalStateException("Could not load RoomLock matrices", e);
        }
    }

    public RoomLockProfile register(List<List<ScanResult>> scans) {
        double[][] xSamples = encode(scans);
        double[] xMean = mean(xSamples);
        double[] bReg = round(matVec(h, xMean));
        double[] cReg = matVec(g, bReg);
        double[] dist = subtract(cReg, xMean);

        double[][] bSamples = new double[xSamples.length][RoomLockEncoder.DIM];
        for (int i = 0; i < xSamples.length; i++) {
            bSamples[i] = matVec(h, add(xSamples[i], dist));
        }

        double[] rad = roundToRadius(multiply(std(bSamples), SIGMA));
        double[] base = mod(bReg, multiply(rad, 2.0));
        return new RoomLockProfile(dist, rad, base, hashVector(xMean));
    }

    public boolean authenticate(RoomLockProfile profile, List<List<ScanResult>> scans) {
        double[] y = mean(encode(scans));
        double[] bAuth = matVec(h, add(y, profile.dist));
        double[] bCell = getLatticeCell(bAuth, profile.base, profile.rad);
        double[] xAuth = subtract(matVec(g, bCell), profile.dist);
        return hashVector(xAuth).equals(profile.passwordHash);
    }

    private double[][] encode(List<List<ScanResult>> scans) {
        double[][] vectors = new double[scans.size()][RoomLockEncoder.DIM];
        for (int i = 0; i < scans.size(); i++) {
            vectors[i] = encoder.encode(scans.get(i));
        }
        return vectors;
    }

    private static double[] getLatticeCell(double[] v, double[] base, double[] rad) {
        double[] cell = new double[v.length];
        for (int i = 0; i < v.length; i++) {
            double width = 2.0 * rad[i];
            double k = Math.floor((v[i] - base[i]) / width + 0.5);
            cell[i] = base[i] + 2.0 * k * rad[i];
        }
        return cell;
    }

    private static double[] roundToRadius(double[] values) {
        double[] out = new double[values.length];
        for (int i = 0; i < values.length; i++) {
            double value = values[i];
            double intPart = Math.floor(value);
            double frac = value - intPart;
            if (frac < 0.5) {
                out[i] = intPart + 0.5;
            } else if (frac == 0.5) {
                out[i] = value;
            } else {
                out[i] = Math.ceil(value);
            }
        }
        return out;
    }

    private static double[] mean(double[][] samples) {
        double[] mean = new double[RoomLockEncoder.DIM];
        for (double[] sample : samples) {
            for (int i = 0; i < mean.length; i++) {
                mean[i] += sample[i];
            }
        }
        for (int i = 0; i < mean.length; i++) {
            mean[i] /= samples.length;
        }
        return mean;
    }

    private static double[] std(double[][] samples) {
        double[] mean = mean(samples);
        double[] variance = new double[RoomLockEncoder.DIM];
        for (double[] sample : samples) {
            for (int i = 0; i < variance.length; i++) {
                double diff = sample[i] - mean[i];
                variance[i] += diff * diff;
            }
        }
        for (int i = 0; i < variance.length; i++) {
            variance[i] = Math.sqrt(variance[i] / samples.length);
        }
        return variance;
    }

    private static double[] matVec(double[][] matrix, double[] vector) {
        double[] out = new double[matrix.length];
        for (int row = 0; row < matrix.length; row++) {
            double sum = 0.0;
            for (int col = 0; col < vector.length; col++) {
                sum += matrix[row][col] * vector[col];
            }
            out[row] = sum;
        }
        return out;
    }

    private static double[] round(double[] values) {
        double[] out = new double[values.length];
        for (int i = 0; i < values.length; i++) {
            out[i] = Math.rint(values[i]);
        }
        return out;
    }

    private static double[] add(double[] left, double[] right) {
        double[] out = new double[left.length];
        for (int i = 0; i < out.length; i++) {
            out[i] = left[i] + right[i];
        }
        return out;
    }

    private static double[] subtract(double[] left, double[] right) {
        double[] out = new double[left.length];
        for (int i = 0; i < out.length; i++) {
            out[i] = left[i] - right[i];
        }
        return out;
    }

    private static double[] multiply(double[] values, double scalar) {
        double[] out = new double[values.length];
        for (int i = 0; i < out.length; i++) {
            out[i] = values[i] * scalar;
        }
        return out;
    }

    private static double[] mod(double[] values, double[] mods) {
        double[] out = new double[values.length];
        for (int i = 0; i < out.length; i++) {
            out[i] = ((values[i] % mods[i]) + mods[i]) % mods[i];
        }
        return out;
    }

    private static String hashVector(double[] vector) {
        try {
            ByteBuffer buffer = ByteBuffer.allocate(vector.length * 4).order(ByteOrder.LITTLE_ENDIAN);
            for (double value : vector) {
                buffer.putFloat((float) value);
            }
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(buffer.array());
            StringBuilder hex = new StringBuilder(hash.length * 2);
            for (byte b : hash) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (Exception e) {
            throw new IllegalStateException("Could not hash RoomLock vector", e);
        }
    }

    private static String readAsset(Context context, String name) throws Exception {
        try (InputStream input = context.getAssets().open(name);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) {
                output.write(buffer, 0, read);
            }
            return output.toString("UTF-8");
        }
    }

    private static double[][] readMatrix(JSONArray rows) throws Exception {
        double[][] matrix = new double[rows.length()][];
        for (int i = 0; i < matrix.length; i++) {
            JSONArray row = rows.getJSONArray(i);
            matrix[i] = new double[row.length()];
            for (int j = 0; j < matrix[i].length; j++) {
                matrix[i][j] = row.getDouble(j);
            }
        }
        return matrix;
    }
}
