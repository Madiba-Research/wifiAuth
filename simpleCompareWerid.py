from glob import glob
import json
import numpy as np
from sklearn.decomposition import PCA
from scipy.stats import pearsonr
import re

# this is for comparing two scans directly, with some basic feature


user_dict = {}

sim_threshold = 0.6


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


def register_json(username: str, scan_json: list):
    global user_dict
    global sim_threshold
    register_scan = compute_mean_scan(scan_json)
    user_dict[username] = register_scan
    # print(f"Registered user: {username}, registered scan: {register_scan}")


def compute_mean_scan(scan_json: list):
    ap_dict = {}
    for scan in scan_json:
        for ap in scan:
            bssid = ap['bssid']
            rssi = ap['rssi']
            if bssid not in ap_dict:
                ap_dict[bssid] = []
            ap_dict[bssid].append(rssi)
    for bssid in ap_dict:
        ap_dict[bssid] = sum(ap_dict[bssid]) / len(ap_dict[bssid])
    return ap_dict


def authenticate_json(username: str, scan_json: list):
    global user_dict
    global sim_threshold
    if username not in user_dict:
        print(f"User {username} not registered.")
        return False
    
    register_scan = user_dict[username]
    auth_scan = compute_mean_scan(scan_json)

    sim_score = calc_sim_score(register_scan, auth_scan)
    print(f"Authenticating user: {username}, similarity score: {sim_score:.4f}")
    return sim_score >= sim_threshold


def calc_sim_score(scan1: dict, scan2: dict) -> float:
    # check common aps:
    # calculate IoU
    keys1 = set(scan1.keys())
    keys2 = set(scan2.keys())
    common_keys = keys1.intersection(keys2)
    union_keys = keys1.union(keys2)
    if not common_keys:
        return 0.0
    overlap_ratio = len(common_keys) / len(union_keys)

    # for common aps, calculate pcc
    # https://en.wikipedia.org/wiki/Pearson_correlation_coefficient
    x = np.array([scan1[b] for b in common_keys])
    x = -1 * x  # convert to positive values
    y = np.array([scan2[b] for b in common_keys])
    y = -1 * y  # convert to positive values

    r, _ = pearsonr(x, y)
    if np.isnan(r):
        return 0.0
    
    slope = None
    slope = compute_slope_pca(x, y)
    if slope > 1:
        slope = 1 / slope

    # print(f"  Overlap ratio: {overlap_ratio:.4f}, PCC: {r:.4f}, slope: {slope:.4f}")
    return overlap_ratio * r * slope
    

    

def compute_slope_pca(x, y):
    data = np.vstack([x, y]).T
    if len(x) < 2:
        return None
    pca = PCA(n_components=2)
    pca.fit(data)
    v = pca.components_[0]  # first principal component vector [v_x, v_y]
    if np.isclose(v[0], 0):
        return None
    slope = v[1] / v[0]
    return slope






if __name__ == "__main__":

    # # read register log
    # REG_DIR = "./log_reg_distance"
    # reg_files = glob(f"{REG_DIR}/*.log")
    # reg_list = []
    # for reg_file in reg_files:
    #     reg_list.extend(extract_JSON_from_log(reg_file))

    # reg_list_filtered = [item for item in reg_list if "p1" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d1p1", "d3p1")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

    # reg_list_filtered = [item for item in reg_list if "p2" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d1p2", "d2p2")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

    # # =======================================================
    # # auth data
    # AUTH_DIR = "./log_auth_distance"
    # # normal d3p2 auth first
    # auth_results = []
    # auth_files = glob(f"{AUTH_DIR}/*_d2p2.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"]
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     auth_results.append(authenticate_json(user, aps))
    # success_rate = sum(auth_results) / len(auth_results)
    # tar_1 = success_rate
    # print(f"Authentication success rate for d2p2: {success_rate:.4f}")

    # # use d1p1, generate d3p1, on model d3
    # auth_results = []
    # auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p1")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     auth_results.append(authenticate_json(user, aps))
    #     # exit()
    # success_rate = sum(auth_results) / len(auth_results)
    # tar_2 = success_rate
    # print(f"Authentication success rate for d3p1: {success_rate:.4f}")
    # # p2 & p1 cross testing
    # # user d3p1(d1p1) authenticate d3p3
    # auth_results = []
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d2p2")
    #     aps = auth["aps"]
    #     auth_results.append(authenticate_json(user, aps))
    # success_rate = sum(auth_results) / len(auth_results)
    # far_1 = success_rate
    # print(f"Authentication success rate for d2p2 (from d3p1): {success_rate:.4f}")
    # # user d3p2 authenticate d3p1
    # auth_results = []
    # auth_files = glob(f"{AUTH_DIR}/*_d2p2.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d2p2", "d3p1")
    #     aps = auth["aps"]
    #     auth_results.append(authenticate_json(user, aps))
    # success_rate = sum(auth_results) / len(auth_results)
    # far_2 = success_rate
    # print(f"Authentication success rate for d3p1 (from d2p2): {success_rate:.4f}")

    # overall_tar = (tar_1 + tar_2) / 2
    # overall_far = (far_1 + far_2) / 2
    # print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")

    # REG_DIR = "./log_reg_distance"
    # reg_list = []
    # reg_list.extend(extract_JSON_from_log(f"{REG_DIR}/auth_app_20250706_171844_reg1.log"))
    # reg_list_filtered = [item for item in reg_list if "t0d1p1" == item.get("username")]
    # register_json(reg_list_filtered[0].get("username"), reg_list_filtered[0].get("aps"))




    # exit()



    # read register log
    REG_DIR = "./log_reg_distance"
    reg_files = glob(f"{REG_DIR}/*.log")
    reg_list = []
    for reg_file in reg_files:
        reg_list.extend(extract_JSON_from_log(reg_file))

    reg_list_filtered = [item for item in reg_list if "p3" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d2p3", "d3p3")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)

    reg_list_filtered = [item for item in reg_list if "p2" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d1p2", "d2p2")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)

    # =======================================================
    # auth data
    AUTH_DIR = "./log_auth_distance"
    # normal d3p2 auth first
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d2p2.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"]
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps))
    success_rate = sum(auth_results) / len(auth_results)
    tar_1 = success_rate
    print(f"Authentication success rate for d2p2: {success_rate:.4f}")

    # use d1p1, generate d3p1, on model d3
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d3p3", "d3p3")
        aps = auth["aps"]
        # print(f"authenticating {user} with {aps}")
        auth_results.append(authenticate_json(user, aps))
        # exit()
    success_rate = sum(auth_results) / len(auth_results)
    tar_2 = success_rate
    print(f"Authentication success rate for d3p3: {success_rate:.4f}")
    # p2 & p1 cross testing
    # user d3p1(d1p1) authenticate d3p3
    auth_results = []
    for auth in auth_list:
        user = auth["username"].replace("d3p3", "d2p2")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps))
    success_rate = sum(auth_results) / len(auth_results)
    far_1 = success_rate
    print(f"Authentication success rate for d2p2 (from d3p1): {success_rate:.4f}")
    # user d3p2 authenticate d3p1
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d2p2.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d2p2", "d3p3")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps))
    success_rate = sum(auth_results) / len(auth_results)
    far_2 = success_rate
    print(f"Authentication success rate for d3p3 (from d2p2): {success_rate:.4f}")

    overall_tar = (tar_1 + tar_2) / 2
    overall_far = (far_1 + far_2) / 2
    print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")




    # # read register log
    # REG_DIR = "./log_reg_distance"
    # reg_files = glob(f"{REG_DIR}/*.log")
    # reg_list = []
    # for reg_file in reg_files:
    #     reg_list.extend(extract_JSON_from_log(reg_file))

    # reg_list_filtered = [item for item in reg_list if "p1" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d1p1", "d3p1")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

    # reg_list_filtered = [item for item in reg_list if "p3" in item.get("username")]
    # for reg in reg_list_filtered:
    #     user_name = reg.get("username").replace("d2p3", "d3p3")
    #     scan_json = reg.get("aps")
    #     register_json(user_name, scan_json)

    # # =======================================================
    # # auth data
    # AUTH_DIR = "./log_auth_distance"
    # # normal d3p3 auth first
    # auth_results = []
    # auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"]
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     auth_results.append(authenticate_json(user, aps))
    # success_rate = sum(auth_results) / len(auth_results)
    # tar_1 = success_rate
    # print(f"Authentication success rate for d3p3: {success_rate:.4f}")

    # # use d1p1, generate d3p1, on model d3
    # auth_results = []
    # auth_files = glob(f"{AUTH_DIR}/*_d1p1.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p1")
    #     aps = auth["aps"]
    #     # print(f"authenticating {user} with {aps}")
    #     auth_results.append(authenticate_json(user, aps))
    #     # exit()
    # success_rate = sum(auth_results) / len(auth_results)
    # tar_2 = success_rate
    # print(f"Authentication success rate for d3p1: {success_rate:.4f}")
    # # p3 & p1 cross testing
    # # user d3p1(d1p1) authenticate d3p3
    # auth_results = []
    # for auth in auth_list:
    #     user = auth["username"].replace("d1p1", "d3p3")
    #     aps = auth["aps"]
    #     auth_results.append(authenticate_json(user, aps))
    # success_rate = sum(auth_results) / len(auth_results)
    # far_1 = success_rate
    # print(f"Authentication success rate for d3p3 (from d3p1): {success_rate:.4f}")
    # # user d3p3 authenticate d3p1
    # auth_results = []
    # auth_files = glob(f"{AUTH_DIR}/*_d3p3.log")
    # auth_list = []
    # for auth_file in auth_files:
    #     auth_list.extend(extract_JSON_from_log(auth_file))
    # for auth in auth_list:
    #     user = auth["username"].replace("d3p3", "d3p1")
    #     aps = auth["aps"]
    #     auth_results.append(authenticate_json(user, aps))
    # success_rate = sum(auth_results) / len(auth_results)
    # far_2 = success_rate
    # print(f"Authentication success rate for d3p1 (from d3p3): {success_rate:.4f}")

    # overall_tar = (tar_1 + tar_2) / 2
    # overall_far = (far_1 + far_2) / 2
    # print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")

    # # =======================================================

# based on our test, 1 meter distance test result:
# Overall TAR: 0.8200, Overall FAR: 0.6800

# 1 meter distance
# Overall TAR: 0.8800, Overall FAR: 0.5800
 
# 3 meter distance test result:
# Overall TAR: 0.9000, Overall FAR: 0.2400
