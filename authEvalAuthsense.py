from glob import glob
import json
import numpy as np
import re
import torch
import torch.nn.functional as F

from models.Encoderfuzzy3 import GNNEncoder, AuthSenseSiemase
from utils.ProcessRawData import create_pyg_graph



user_dict = {}

def extract_JSON_from_log(file_path: str) -> list:
    """
    Extract JSON objects from a log file.
    """

    json_list = []

    with open(file_path, 'r') as file:
        for log_line in file:
            match = re.search(r'({.*})', log_line)
            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                # print(data)
                json_list.append(data)
    return json_list


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


def load_authsense_model(model_path, input_dim=6, hidden_dim=64, output_dim=32):

    encoder = GNNEncoder(input_dim, hidden_dim, output_dim)
    
    model = AuthSenseSiemase(encoder)
    
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    return model


def extract_components(model):
    encoder = model.embedding_net
    decision_net = model.decision_net

    encoder.eval()
    decision_net.eval()
    
    return encoder, decision_net


# def get_averaged_embedding(encoder, graph_list, n_samples=10):

#     embeddings = []
    
#     with torch.no_grad():
#         samples = graph_list[:n_samples]
        
#         for g in samples:
#             g = g.to(device)
#             emb = encoder(g.x, g.edge_index, g.batch, g.edge_attr)
#             embeddings.append(emb)
        
#         averaged_emb = torch.stack(embeddings).mean(dim=0)
    
#     return averaged_emb


def similarity_from_two_embeddings(emb1, emb2, decision_net):
    output1 = F.normalize(emb1, p=2, dim=1)
    output2 = F.normalize(emb2, p=2, dim=1)

    # print("output1:", output1)
    # print("output2:", output2)

    distance = (output1 - output2) ** 2
    # distance = distance.squeeze()
    # if distance.dim() == 1:
    #     distance = distance.unsqueeze(0)
    # print("distance:", distance)
    # print("distance shape:", distance.shape)
    # distance = torch.norm(output1 - output2, p=2, dim=1, keepdim=True)
    decision = decision_net(distance)
    # return decision, decision.item() > 0.5
    return decision, decision.item() > 0.477


def encode_vec_from_ap_json(ap, encoder_model):
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


def get_vec_from_aps(ap_list, encoder_model):
    vecs = []
    for ap in ap_list:
        vec = encode_vec_from_ap_json(ap, encoder_model)
        vecs.append(vec)
    vecs = np.array(vecs)
    register_vec = np.mean(vecs, axis=0)
    return register_vec



def register_json(username: str, scan_json: list, encoder_model):
    global user_dict
    register_vec = get_vec_from_aps(scan_json, encoder_model)
    user_dict[username] = register_vec
    print(f"Registered user: {username}, vector shape: {register_vec.shape}")


def authenticate_json(username: str, scan_json: list, encoder_model, decision_net):
    global user_dict
    if username not in user_dict:
        print(f"User {username} not registered.")
        return False
    register_vec = user_dict[username]
    auth_vec = get_vec_from_aps(scan_json, encoder_model)

    reg_tensor = torch.tensor(register_vec, dtype=torch.float32).to(device)
    auth_tensor = torch.tensor(auth_vec, dtype=torch.float32).to(device)

    if reg_tensor.dim() == 1:
        reg_tensor = reg_tensor.unsqueeze(0)
    if auth_tensor.dim() == 1:
        auth_tensor = auth_tensor.unsqueeze(0)

    decision, is_auth = similarity_from_two_embeddings(
        reg_tensor,
        auth_tensor,
        decision_net
    )
    # print(f"Authentication result for user {username}: {is_auth}, decision score: {decision.item():.4f}")
    return is_auth



if __name__ == "__main__":
    authsense_model_path = "best_630d3norm_authsense.pth"
    authsense_model = load_authsense_model(authsense_model_path)
    encoder, decision_net = extract_components(authsense_model)

    # register data
    REG_DIR = "./log_reg_distance"
    reg_files = glob(f"{REG_DIR}/*.log")
    reg_list = []
    for reg_file in reg_files:
        reg_list.extend(extract_JSON_from_log(reg_file))

    reg_list_filtered = [item for item in reg_list if "p1" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d1p1", "d3p1")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json, encoder)

    reg_list_filtered = [item for item in reg_list if "p3" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d2p3", "d3p3")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json, encoder)


    reg_list_filtered = [item for item in reg_list if "p5" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d5p5", "d3p5")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json, encoder)

    reg_list_filtered = [item for item in reg_list if "p7" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d5p7", "d3p7")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json, encoder)


    # =======================================================
    # auth data
    AUTH_DIR = "./log_auth_distance"
    # normal d3p3 auth first
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"]
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    tar_1 = success_rate
    print(f"Authentication success rate for d3p3: {success_rate:.4f}")

    # use d1p1, generate d3p1, on model d3
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p1")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
        # exit()
    success_rate = sum(auth_results) / len(auth_results)
    tar_2 = success_rate
    print(f"Authentication success rate for d3p1: {success_rate:.4f}")
    # p3 & p1 cross testing
    # user d3p1(d1p1) authenticate d3p3
    auth_results = []
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p3")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    far_1 = success_rate
    print(f"Authentication success rate for d3p3 (from d3p1): {success_rate:.4f}")
    # user d3p3 authenticate d3p1
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d3p3", "d3p1")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    far_2 = success_rate
    print(f"Authentication success rate for d3p1 (from d3p3): {success_rate:.4f}")

    overall_tar = (tar_1 + tar_2) / 2
    overall_far = (far_1 + far_2) / 2
    print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")

    # =======================================================

    AUTH_DIR = "./log_auth_distance_sigma2"
    # # normal d1p1 auth first for d5
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d5p5.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d5p5", "d3p5")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    tar_1 = success_rate
    print(f"Authentication success rate for d3p1: {success_rate:.4f}")

    # use d1p1, generate d3p1, on model d3
    auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    auth_results = []
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p1")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    tar_2 = success_rate
    print(f"Authentication success rate for d3p1: {success_rate:.4f}")
    # p3 & p1 cross testing
    # user d3p1(d1p1) authenticate d3p3
    auth_results = []
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p5")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    far_1 = success_rate
    print(f"Authentication success rate for d3p5 (from d3p1): {success_rate:.4f}")
    # user d3p3 authenticate d3p1
    auth_files = glob(f"{AUTH_DIR}/*_d5p5.log")
    auth_results = []
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d5p5", "d3p1")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    far_2 = success_rate
    print(f"Authentication success rate for d3p1 (from d3p5): {success_rate:.4f}")

    overall_tar = (tar_1 + tar_2) / 2
    overall_far = (far_1 + far_2) / 2
    print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")

    #======================================================

    AUTH_DIR = "./log_auth_distance_sigma2"
    # # normal d1p1 auth first for d5p7
    auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    auth_list = []
    auth_results = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d5p7", "d3p7")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    tar_1 = success_rate
    print(f"Authentication success rate for d3p7: {success_rate:.4f}")

    # use d1p1, generate d3p1, on model d3
    auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    auth_results = []
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p1")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    tar_2 = success_rate
    print(f"Authentication success rate for d3p1: {success_rate:.4f}")
    # p7 & p1 cross testing
    # user d3p1(d1p1) authenticate d5p7
    auth_results = []
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p7")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    far_1 = success_rate
    print(f"Authentication success rate for d3p7 (from d3p1): {success_rate:.4f}")
    # user d3p3 authenticate d3p1
    auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    auth_results = []
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d5p7", "d3p1")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    success_rate = sum(auth_results) / len(auth_results)
    far_2 = success_rate
    print(f"Authentication success rate for d3p1 (from d3p7): {success_rate:.4f}")

    overall_tar = (tar_1 + tar_2) / 2
    overall_far = (far_1 + far_2) / 2
    print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")

    



