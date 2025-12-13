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

    # return decision, decision.item() > 0.477
    # Overall True acceptance rate (TAR): 94.89%, False rejection rate (FRR): 5.11%
    # Overall False acceptance rate (FAR): 35.32%

    # return decision, decision.item() > 0.481
    # Overall True acceptance rate (TAR): 94.89%, False rejection rate (FRR): 5.11%
    # Overall False acceptance rate (FAR): 29.79%

    # return decision, decision.item() > 0.485
    # Overall True acceptance rate (TAR): 94.26%, False rejection rate (FRR): 5.74%
    # Overall False acceptance rate (FAR): 24.47%

    # return decision, decision.item() > 0.490
    # Overall True acceptance rate (TAR): 91.91%, False rejection rate (FRR): 8.09%
    # Overall False acceptance rate (FAR): 17.45%

    # return decision, decision.item() > 0.494
    # Overall True acceptance rate (TAR): 83.5%
    # Overall False acceptance rate (FAR): 7.5%

    # return decision, decision.item() > 0.49
    # Overall True acceptance rate (TAR): 86.%
    # Overall False acceptance rate (FAR): 10.5%

    return decision, decision.item() > 0.488
    # Overall True acceptance rate (TAR): 86.5%
    # Overall False acceptance rate (FAR): 13%


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

    # # register data
    # REG_DIR = "./log_reg_distance"
    # reg_files = glob(f"{REG_DIR}/*.log")
    # reg_list = []
    # for reg_file in reg_files:
    #     reg_list.extend(extract_JSON_from_log(reg_file))

    # reg_list_filtered = [item for item in reg_list if "p1" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d1p1", "d3p1")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json, encoder)

    # # reg_list_filtered = [item for item in reg_list if "p3" in item.get("username")]
    # # for reg in reg_list_filtered:
    # #     user_name = reg.get("username").replace("d2p3", "d3p3")
    # #     scan_json = reg.get("aps")
    # #     register_json(user_name, scan_json, encoder)


    # # reg_list_filtered = [item for item in reg_list if "p5" in item.get("username")]
    # # for reg in reg_list_filtered:
    # #     user_name = reg.get("username").replace("d5p5", "d3p5")
    # #     scan_json = reg.get("aps")
    # #     register_json(user_name, scan_json, encoder)

    # reg_list_filtered = [item for item in reg_list if "p7" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d5p7", "d3p7")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json, encoder)


    # register with another 20 users
    ANOTHER_REG_DIR = "./another20loc"
    reg_files = glob(f"{ANOTHER_REG_DIR}/*.log")
    reg_auth_list = []
    for reg_file in reg_files:
        reg_auth_list.extend(extract_JSON_from_log(reg_file))
    reg_list = [reg for reg in reg_auth_list if reg["operation"] == "register"]

    user_list = ["t" + str(i) for i in range(6, 25)]
    for reg in reg_list:
        user_name = reg.get("username")[: -2] + "d3" + reg.get("username")[-2 :]
        # print(f'registering user: {username}')
        scan_json = reg.get("aps")
        register_json(user_name, scan_json, encoder)


    # =======================================================
    # auth data

    overall_tp_1 = 0
    overall_total_1 = 0
    overall_tp_2 = 0
    overall_total_2 = 0
    overall_fp_1 = 0
    overall_total_3 = 0
    overall_fp_2 = 0
    overall_total_4 = 0

    # AUTH_DIR = "./log_auth_distance_sigma2"
    # # # normal d1p1 auth first for d5p7
    # auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    # auth_list = []
    # auth_results = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d5p7", "d3p7")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    # success_rate = sum(auth_results) / len(auth_results)
    # tar_1 = success_rate
    # overall_tp_1 += sum(auth_results)
    # overall_total_1 += len(auth_results)
    # print(f"Authentication success rate for d3p7: {success_rate:.4f}")

    # # use d1p1, generate d3p1, on model d3
    # auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    # auth_results = []
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p1")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    # success_rate = sum(auth_results) / len(auth_results)
    # tar_2 = success_rate
    # overall_tp_2 += sum(auth_results)
    # overall_total_2 += len(auth_results)
    # print(f"Authentication success rate for d3p1: {success_rate:.4f}")
    # # p7 & p1 cross testing
    # # user d3p1(d1p1) authenticate d5p7
    # auth_results = []
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p7")
    #     aps = auth["aps"]
    #     auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    # success_rate = sum(auth_results) / len(auth_results)
    # far_1 = success_rate
    # overall_fp_1 += sum(auth_results)
    # overall_total_3 += len(auth_results)
    # print(f"Authentication success rate for d3p7 (from d3p1): {success_rate:.4f}")
    # # user d3p3 authenticate d3p1
    # auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    # auth_results = []
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d5p7", "d3p1")
    #     aps = auth["aps"]
    #     auth_results.append(authenticate_json(user, aps, encoder, decision_net))
    # success_rate = sum(auth_results) / len(auth_results)
    # far_2 = success_rate
    # overall_fp_2 += sum(auth_results)
    # overall_total_4 += len(auth_results)
    # print(f"Authentication success rate for d3p1 (from d3p7): {success_rate:.4f}")

    # overall_tar = (tar_1 + tar_2) / 2
    # overall_far = (far_1 + far_2) / 2
    # print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")

    # auth another 20 users
    ANOTHER_AUTH_DIR = "./another20loc"
    auth_files = glob(f"{ANOTHER_AUTH_DIR}/*.log")
    reg_auth_list = []
    for auth_file in auth_files:
        reg_auth_list.extend(extract_JSON_from_log(auth_file))
    auth_list = [auth for auth in reg_auth_list if auth["operation"] == "authenticate"]

    user_name_list = ["t" + str(i) for i in range(6, 25)]
    for user_name in user_name_list:

        # # t6, t7, t11, t12, t21
        if user_name == "t6" or user_name == "t7" or user_name == "t11" or user_name == "t12" or user_name == "t21":
            continue
        # for evaluation datsest
        # if user_name != "t8" and user_name != "t9" and user_name != "t10" and user_name != "t13" and user_name != "t15":
        #     continue
        # for test dataset
        if user_name == "t8" or user_name == "t9" or user_name == "t10" or user_name == "t13" or user_name == "t15":
            continue


        user_1 = user_name + "p1"
        print("user_1:", user_1)
        user_1_auth = [auth for auth in auth_list if auth["username"] == user_1]
        print(f'user_1_auth count: {len(user_1_auth)}')

        user_7 = user_name + "p7"
        print("user_7:", user_7)
        user_7_auth = [auth for auth in auth_list if auth["username"] == user_7]
        print(f'user_7_auth count: {len(user_7_auth)}')

        # user 7 first, follow above
        auth_results = []
        for auth in user_7_auth:
            username_7 = user_name + "d3p7"
            aps = auth["aps"]
            auth_results.append(authenticate_json(username_7, aps, encoder, decision_net))
            overall_tp_1 += sum(auth_results)
            overall_total_1 += len(auth_results)
            print(f'user: {username_7}, auth response: {auth_results[-1]}')
        
        # user 1
        auth_results = []
        for auth in user_1_auth:
            username_1 = user_name + "d3p1"
            aps = auth["aps"]
            auth_results.append(authenticate_json(username_1, aps, encoder, decision_net))
            overall_tp_2 += sum(auth_results)
            overall_total_2 += len(auth_results)
            print(f'user: {username_1}, auth response: {auth_results[-1]}')

        auth_results = []
        for auth in user_1_auth:
            username_7 = user_name + "d3p7"
            aps = auth["aps"]
            auth_results.append(authenticate_json(username_7, aps, encoder, decision_net))
            overall_fp_1 += sum(auth_results)
            overall_total_3 += len(auth_results)
            print(f'user: {username_7}, auth response: {auth_results[-1]}')

        auth_results = []
        for auth in user_7_auth:
            username_1 = user_name + "d3p1"
            aps = auth["aps"]
            auth_results.append(authenticate_json(username_1, aps, encoder, decision_net))
            overall_fp_2 += sum(auth_results)
            overall_total_4 += len(auth_results)
            print(f'user: {username_1}, auth response: {auth_results[-1]}')

    print("Overall True acceptance rate (TAR): {:.2f}%".format((overall_tp_1 + overall_tp_2) / (overall_total_1 + overall_total_2) * 100 if (overall_total_1 + overall_total_2) > 0 else 0))
    # print("Overall False Rejection rate (FRR): {:.2f}%".format(100 - (overall_tp_1 + overall_tp_2) / (overall_total_1 + overall_total_2) * 100 if (overall_total_1 + overall_total_2) > 0 else 0))
    print("Overall False acceptance rate (FAR): {:.2f}%".format((overall_fp_1 + overall_fp_2) / (overall_total_3 + overall_total_4) * 100 if (overall_total_3 + overall_total_4) > 0 else 0))

    



