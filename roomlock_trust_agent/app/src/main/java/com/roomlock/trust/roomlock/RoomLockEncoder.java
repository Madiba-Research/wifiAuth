package com.roomlock.trust.roomlock;

import android.content.Context;
import android.net.wifi.ScanResult;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public final class RoomLockEncoder {
    public static final int DIM = 32;

    private final Layer[] layers;
    private final BatchNorm[] batchNorms;
    private final double batchNormEps;

    public RoomLockEncoder(Context context) {
        try {
            JSONObject weights = new JSONObject(readAsset(context, "roomlock_gnn_weights.json"));
            batchNormEps = weights.getDouble("batchNormEps");

            JSONArray layerArray = weights.getJSONArray("layers");
            layers = new Layer[layerArray.length()];
            for (int i = 0; i < layers.length; i++) {
                layers[i] = Layer.fromJson(layerArray.getJSONObject(i));
            }

            JSONArray bnArray = weights.getJSONArray("batchNorms");
            batchNorms = new BatchNorm[bnArray.length()];
            for (int i = 0; i < batchNorms.length; i++) {
                batchNorms[i] = BatchNorm.fromJson(bnArray.getJSONObject(i));
            }
        } catch (Exception e) {
            throw new IllegalStateException("Could not load RoomLock GNN weights", e);
        }
    }

    public double[] encode(List<ScanResult> scanResults) {
        Graph graph = createGraph(scanResults);
        double[][] x = graph.nodeFeatures;

        x = conv(x, graph.edgeAttr, layers[0]);
        relu(x);
        batchNorm(x, batchNorms[0]);

        x = conv(x, graph.edgeAttr, layers[1]);
        relu(x);
        batchNorm(x, batchNorms[1]);

        x = conv(x, graph.edgeAttr, layers[2]);
        relu(x);
        batchNorm(x, batchNorms[2]);

        x = conv(x, graph.edgeAttr, layers[3]);
        return meanPool(x);
    }

    private double[][] conv(double[][] x, double[] edgeAttr, Layer layer) {
        double[][] out = new double[x.length][layer.outDim()];
        double[] rootValue = linear(x[0], layer.valueWeight, layer.valueBias);

        for (int node = 0; node < x.length; node++) {
            double[] value = linear(x[node], layer.skipWeight, layer.skipBias);
            if (node > 0) {
                double rssi = edgeAttr[node - 1];
                for (int j = 0; j < value.length; j++) {
                    value[j] += rootValue[j] + layer.edgeWeight[j][0] * rssi;
                }
            }
            out[node] = value;
        }
        return out;
    }

    private static Graph createGraph(List<ScanResult> scanResults) {
        List<double[]> nodes = new ArrayList<>();
        List<Double> edgeAttrs = new ArrayList<>();
        nodes.add(new double[]{0, 0, 0, 0, 0, 0});

        if (scanResults != null) {
            for (ScanResult result : scanResults) {
                double[] bssid = macToFeature(result.BSSID);
                if (bssid == null) {
                    continue;
                }
                nodes.add(bssid);
                edgeAttrs.add((result.level + 100.0) / 100.0);
            }
        }

        double[][] nodeFeatures = nodes.toArray(new double[0][]);
        double[] attrs = new double[edgeAttrs.size()];
        for (int i = 0; i < attrs.length; i++) {
            attrs[i] = edgeAttrs.get(i);
        }
        return new Graph(nodeFeatures, attrs);
    }

    private static double[] macToFeature(String mac) {
        if (mac == null) {
            return null;
        }
        String clean = mac.replace(":", "").toLowerCase(Locale.US);
        if (clean.length() < 12) {
            return null;
        }

        double[] feature = new double[6];
        try {
            for (int i = 0; i < feature.length; i++) {
                feature[i] = Integer.parseInt(clean.substring(i * 2, i * 2 + 2), 16);
            }
            return feature;
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static double[] linear(double[] input, double[][] weight, double[] bias) {
        double[] out = new double[weight.length];
        for (int row = 0; row < weight.length; row++) {
            double sum = bias[row];
            for (int col = 0; col < input.length; col++) {
                sum += weight[row][col] * input[col];
            }
            out[row] = sum;
        }
        return out;
    }

    private static void relu(double[][] x) {
        for (double[] row : x) {
            for (int i = 0; i < row.length; i++) {
                row[i] = Math.max(0.0, row[i]);
            }
        }
    }

    private void batchNorm(double[][] x, BatchNorm bn) {
        for (double[] row : x) {
            for (int i = 0; i < row.length; i++) {
                row[i] = (row[i] - bn.runningMean[i])
                        / Math.sqrt(bn.runningVar[i] + batchNormEps)
                        * bn.weight[i]
                        + bn.bias[i];
            }
        }
    }

    private static double[] meanPool(double[][] x) {
        double[] pooled = new double[x[0].length];
        for (double[] row : x) {
            for (int i = 0; i < pooled.length; i++) {
                pooled[i] += row[i];
            }
        }
        for (int i = 0; i < pooled.length; i++) {
            pooled[i] /= x.length;
        }
        return pooled;
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

    private static double[] readVector(JSONArray array) throws Exception {
        double[] vector = new double[array.length()];
        for (int i = 0; i < vector.length; i++) {
            vector[i] = array.getDouble(i);
        }
        return vector;
    }

    private static final class Graph {
        final double[][] nodeFeatures;
        final double[] edgeAttr;

        Graph(double[][] nodeFeatures, double[] edgeAttr) {
            this.nodeFeatures = nodeFeatures;
            this.edgeAttr = edgeAttr;
        }
    }

    private static final class Layer {
        final double[][] valueWeight;
        final double[] valueBias;
        final double[][] edgeWeight;
        final double[][] skipWeight;
        final double[] skipBias;

        Layer(double[][] valueWeight, double[] valueBias, double[][] edgeWeight,
              double[][] skipWeight, double[] skipBias) {
            this.valueWeight = valueWeight;
            this.valueBias = valueBias;
            this.edgeWeight = edgeWeight;
            this.skipWeight = skipWeight;
            this.skipBias = skipBias;
        }

        int outDim() {
            return skipBias.length;
        }

        static Layer fromJson(JSONObject object) throws Exception {
            return new Layer(
                    readMatrix(object.getJSONArray("valueWeight")),
                    readVector(object.getJSONArray("valueBias")),
                    readMatrix(object.getJSONArray("edgeWeight")),
                    readMatrix(object.getJSONArray("skipWeight")),
                    readVector(object.getJSONArray("skipBias")));
        }
    }

    private static final class BatchNorm {
        final double[] weight;
        final double[] bias;
        final double[] runningMean;
        final double[] runningVar;

        BatchNorm(double[] weight, double[] bias, double[] runningMean, double[] runningVar) {
            this.weight = weight;
            this.bias = bias;
            this.runningMean = runningMean;
            this.runningVar = runningVar;
        }

        static BatchNorm fromJson(JSONObject object) throws Exception {
            return new BatchNorm(
                    readVector(object.getJSONArray("weight")),
                    readVector(object.getJSONArray("bias")),
                    readVector(object.getJSONArray("runningMean")),
                    readVector(object.getJSONArray("runningVar")));
        }
    }
}
