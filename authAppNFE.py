# from user import User
# from fuzzyVerifier import RadiusAdaptedFuzzyVerifier
import time
import numpy as np
from flask import Flask, request, jsonify
from authSystemNFE import AuthSystem
from utils.ProcessRawData import create_pyg_graph

import torch
# from models.Encoderfuzzy import TripletNet, GNNEncoder
from models.Encoderfuzzy3 import TripletNet, GNNEncoder
# from models.Encoderfuzzy31 import TripletNet, GNNEncoder

import logging
import json


app = Flask(__name__)

time_now = time.strftime("%Y%m%d_%H%M%S", time.localtime())
logging.basicConfig(
    filename=f'auth_app_{time_now}.log',  # 日志文件名
    level=logging.INFO,       # 日志级别
    format='%(asctime)s %(levelname)s %(message)s'
)

# this is the the authApp but we use to test NFE based method for comparison

# prepare for GNN encoder
# todo: we can make it into a encoder class
device = 'cpu'
encoder_model = GNNEncoder(input_dim=6, hidden_dim=64, output_dim=32).to(device)
triplet_model = TripletNet(encoder_model).to(device)

# checkpoint = torch.load('best_630_model.pth', map_location=device)

# checkpoint = torch.load('best_630d1_model.pth', map_location=device)
# checkpoint = torch.load('best_630d2_model.pth', map_location=device)
# checkpoint = torch.load('best_630d3_model.pth', map_location=device)
# checkpoint = torch.load('best_630d3norm_model.pth', map_location=device)
# checkpoint = torch.load('best_630d3norm_hnm_model.pth', map_location=device)
# checkpoint = torch.load('best_630d3norm_hnm_model3.pth', map_location=device)
# checkpoint = torch.load('best_630d3norm_hnm_model3_mixpool_a2.pth', map_location=device)
# checkpoint = torch.load('best_630d3norm_hnm_model3_mixpool_res_a2.pth', map_location=device)
# checkpoint = torch.load('best_630d3norm_hnm_model3_Alpha30_random.pth', map_location=device)
checkpoint = torch.load('best_630d3norm_hnm_meanpool_a4_random.pth', map_location=device)

print("\n=== Checkpoint Contents ===")
print(f"Epoch: {checkpoint['epoch']}")
print(f"Loss: {checkpoint['loss']:.4f}")
print(f"Accuracy: {checkpoint['accuracy']:.4f}")

triplet_model.load_state_dict(checkpoint['model_state_dict'])
encoder_model.eval()

# notice here the database file
# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "users.db")
# sigma1 means that when registration, we filter out data out of 1 standard deviation
# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "usersd3sigma2.db")
# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "usersd5sigma2.db")
# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "usersd3normsigma2.db")
# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "usersd3normDictsigma2.db")

# model 3 is with 32 dim output
# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "usersd3normDict3sigma2.db")
# auth_system = AuthSystem("H_G_demo_32_dimension.npz", "usersd3normDict3Alpha30sigma2_mixpool_a2.db")
# auth_system = AuthSystem("H_G_demo_32_dimension.npz", "usersd3normDict_main_pool_randomtrain_NFE.db") # please delete extra users beside t0-t4
# auth_system = AuthSystem("H_G_demo_32_dimension.npz", "usersd3normDict_main_pool_randomtrain_NFE_25u.db")
auth_system = AuthSystem("H_G_demo_32_dimension.npz", "usersd3normDict_main_pool_randomtrain_NFE_25u_0045.db")


# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "userswallsigma2.db")
# auth_system = AuthSystem("H_G_demo_8_dimension.npz", "usersd3.db")

# sigma_filter <= 0 is original method, accepting all collected samples
# positive sigma_filter means using standard deviation * sigma_filter as the radius in b space
# sigma_filter = 2

# as mentioned in the paper, user embedded vector are scaled with "a"
# which actually control the noisy radius
# scale_filter = 0.025
# scale_filter = 0.01
scale_filter = 0.045


# in this version, the API receive:
# {
#   "username": "user1",
#   "aps": [ { bssid and rssi info }, ... ]
# }


# @app.route("/backregistercheck", methods=["POST"])
# def back_register_check():
#     try:
#         data = request.get_json()
#         user = data["username"]
#         result = auth_system.register_info_check(user)
#         # todo:
#         return jsonify({"status": "success", "can_register": result})

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 400



# @app.route("/simregister", methods=["POST"])
# def sim_register():
#     """
#     Simulate a registration, for checking b space data, r_b and O_b
#     don't write user info into database
#     """
#     try:
#         data = request.get_json()
#         x_s = [encode_vec_from_ap_json(ap)[0] for ap in data["aps"]]
#         x_s = np.array(x_s)
#         auth_system.sim_register_user(x_s)
#         return jsonify({"status": "success", "message": "Simulation registration successful."})

#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data["username"]

        # x_s = np.array(data["features"])  # Expecting a list of vectors (list of list)
        x_s = [encode_vec_from_ap_json(ap)[0] for ap in data["aps"]]
        x_s = np.array(x_s)

        auth_system.register_user(username, x_s, scale_a=scale_filter)

        # logging
        log_data = {
            "operation": "register",
            "username": username,
            "aps": data["aps"],
            "x_s": x_s.tolist()
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
        # y = np.array(data["feature"])  # Expecting a single vector

        # todo: if possible, we can take average of multiple y, to reduce noise in authentication phase
        # y = encode_vec_from_ap_json(data["aps"][0])
        y_s = [encode_vec_from_ap_json(ap)[0] for ap in data["aps"]]
        y_s = np.array(y_s)
        y = np.mean(y_s, axis=0)
        
        result = auth_system.authenticate_user(username, y, scale_a=scale_filter)

        # logging
        log_data = {
            "operation": "authenticate",
            "username": username,
            "aps": data["aps"],
            "y_s": y_s.tolist(),
            "result": result
        }
        logging.info(f"Authenticate: {json.dumps(log_data)}")

        return jsonify({"status": "success", "authenticated": bool(result)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    




def encode_vec_from_ap_json(ap):
    g = create_pyg_graph(ap, None)
    x = g.x.to(device)
    edge_index = g.edge_index.to(device)
    edge_attr = g.edge_attr.to(device)
    if hasattr(g, 'batch') and g.batch is not None:
        batch = g.batch.to(device)
    else:
        batch = torch.zeros(g.num_nodes, dtype=torch.long).to(device)
    with torch.no_grad():
        output_vec = encoder_model(x, edge_index, batch, edge_attr)
    return output_vec.cpu().numpy()
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    