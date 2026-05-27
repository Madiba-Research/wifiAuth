import time
import json
import logging

import numpy as np
from flask import Flask, request, jsonify

import torch

from authSystemLongAdapt import AuthSystem
from utils.ProcessRawData import create_pyg_graph
from models.Encoderfuzzy3 import TripletNet, GNNEncoder


app = Flask(__name__)

time_now = time.strftime("%Y%m%d_%H%M%S", time.localtime())
logging.basicConfig(
    filename=f"auth_app_long_adapt_{time_now}.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


device = "cpu"
encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=32).to(device)
triplet_model = TripletNet(encoder_model).to(device)
checkpoint = torch.load("best_630d3norm_hnm_meanpool_a4_random.pth", map_location=device)

print("\n=== Checkpoint Contents ===")
print(f"Epoch: {checkpoint['epoch']}")
print(f"Loss: {checkpoint['loss']:.4f}")
print(f"Accuracy: {checkpoint['accuracy']:.4f}")

triplet_model.load_state_dict(checkpoint["model_state_dict"])
encoder_model.eval()


sigma_filter = 1.3
adapt_weight = 0.2

auth_system = AuthSystem(
    "H_G_demo_32_dimension.npz",
    "usersd3normDict_main_pool_longadapt.db",
    default_sigma=sigma_filter,
)


@app.route("/simregister", methods=["POST"])
def sim_register():
    """
    Simulate registration without writing user state into the database.
    """
    try:
        data = request.get_json()
        x_s = [encode_vec_from_ap_json(ap)[0] for ap in data["aps"]]
        x_s = np.array(x_s)
        sim_result = auth_system.sim_register_user(x_s)
        return jsonify(
            {
                "status": "success",
                "message": "Simulation registration successful.",
                "result": serialize_for_json(sim_result),
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data["username"]
        sigma = float(data.get("sigma", sigma_filter))

        x_s = [encode_vec_from_ap_json(ap)[0] for ap in data["aps"]]
        x_s = np.array(x_s)

        auth_system.register_user(username, x_s, sigma=sigma)

        log_data = {
            "operation": "register",
            "username": username,
            "sigma": sigma,
            "aps": data["aps"],
            "x_s": x_s.tolist(),
        }
        logging.info(f"Register: {json.dumps(log_data)}")

        return jsonify({"status": "success", "message": f"User '{username}' registered."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/authenticate", methods=["POST"])
def authenticate():
    try:
        data = request.get_json()
        username = data["username"]
        a = float(data.get("a", adapt_weight))
        sigma = data.get("sigma")
        if sigma is not None:
            sigma = float(sigma)

        y_s = [encode_vec_from_ap_json(ap)[0] for ap in data["aps"]]
        y_s = np.array(y_s)

        result = auth_system.authenticate_user_long_adapt(username, y_s, a=a, sigma=sigma)

        log_data = {
            "operation": "authenticate_long_adapt",
            "username": username,
            "a": a,
            "sigma": sigma,
            "aps": data["aps"],
            "y_s": y_s.tolist(),
            "result": result,
        }
        logging.info(f"AuthenticateLongAdapt: {json.dumps(log_data)}")

        return jsonify({"status": "success", "authenticated": bool(result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


def encode_vec_from_ap_json(ap):
    g = create_pyg_graph(ap, None)
    x = g.x.to(device)
    edge_index = g.edge_index.to(device)
    edge_attr = g.edge_attr.to(device)
    if hasattr(g, "batch") and g.batch is not None:
        batch = g.batch.to(device)
    else:
        batch = torch.zeros(g.num_nodes, dtype=torch.long).to(device)
    with torch.no_grad():
        output_vec = encoder_model(x, edge_index, batch, edge_attr)
    return output_vec.cpu().numpy()


def serialize_for_json(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: serialize_for_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_for_json(item) for item in value]
    return value


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
