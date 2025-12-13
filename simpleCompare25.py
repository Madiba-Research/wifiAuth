from glob import glob
import json
import numpy as np
from sklearn.decomposition import PCA
from scipy.stats import pearsonr
import re

# this is for comparing two scans directly, with some basic feature


user_dict = {}

sim_threshold = 0.5


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


    # read register log
    REG_DIR = "./log_reg_distance"
    reg_files = glob(f"{REG_DIR}/*.log")
    reg_list = []
    for reg_file in reg_files:
        reg_list.extend(extract_JSON_from_log(reg_file))

    reg_list_filtered = [item for item in reg_list if "p1" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d1p1", "d3p1")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)

    reg_list_filtered = [item for item in reg_list if "p7" in item.get("username")]
    for reg in reg_list_filtered:
        user_name = reg.get("username").replace("d5p7", "d3p7")
        scan_json = reg.get("aps")
        register_json(user_name, scan_json)

    

    # =======================================================
    # auth data
    AUTH_DIR = "./log_auth_distance_32"
    # normal d3p2 auth first
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
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
    print(f"Authentication success rate for d7p7: {success_rate:.4f}")

    AUTH_DIR = "./log_auth_distance"
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
        auth_results.append(authenticate_json(user, aps))
        # exit()
    success_rate = sum(auth_results) / len(auth_results)
    tar_2 = success_rate
    print(f"Authentication success rate for d3p1: {success_rate:.4f}")
    # p2 & p1 cross testing
    # user d3p1(d1p1) authenticate d3p3
    auth_results = []
    for auth in auth_list:
        user = auth["username"].replace("d1p1", "d3p7")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps))
    success_rate = sum(auth_results) / len(auth_results)
    far_1 = success_rate
    print(f"Authentication success rate for d3p7 (from d3p1): {success_rate:.4f}")

    # user d3p2 authenticate d3p1
    AUTH_DIR = "./log_auth_distance_32"
    auth_results = []
    auth_files = glob(f"{AUTH_DIR}/*_d7p7.log")
    auth_list = []
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    for auth in auth_list:
        user = auth["username"].replace("d3p7", "d3p1")
        aps = auth["aps"]
        auth_results.append(authenticate_json(user, aps))
    success_rate = sum(auth_results) / len(auth_results)
    far_2 = success_rate
    print(f"Authentication success rate for d3p1 (from d3p7): {success_rate:.4f}")

    overall_tar = (tar_1 + tar_2) / 2
    overall_far = (far_1 + far_2) / 2
    print(f"Overall TAR: {overall_tar:.4f}, Overall FAR: {overall_far:.4f}")

    
    # for remaining 20 users
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
        register_json(user_name, scan_json)

    # auth for another 20 users
    overall_tp_1 = 0
    overall_total_1 = 0
    overall_tp_2 = 0
    overall_total_2 = 0
    overall_fp_1 = 0
    overall_total_3 = 0
    overall_fp_2 = 0
    overall_total_4 = 0

    ANOTHER_AUTH_DIR = "./another20loc"
    auth_files = glob(f"{ANOTHER_AUTH_DIR}/*.log")
    reg_auth_list = []
    for auth_file in auth_files:
        reg_auth_list.extend(extract_JSON_from_log(auth_file))
    auth_list = [auth for auth in reg_auth_list if auth["operation"] == "authenticate"]

    user_name_list = ["t" + str(i) for i in range(6, 25)]
    for user_name in user_name_list:

        # # t6, t7, t11, t12, t21
        # if user_name == "t6" or user_name == "t7" or user_name == "t11" or user_name == "t12" or user_name == "t21":
        #     continue

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
            auth_results.append(authenticate_json(username_7, aps))
            overall_tp_1 += sum(auth_results)
            overall_total_1 += len(auth_results)
            # print(f'user: {username_7}, auth response: {auth_results[-1]}')
        
        # user 1
        auth_results = []
        for auth in user_1_auth:
            username_1 = user_name + "d3p1"
            aps = auth["aps"]
            auth_results.append(authenticate_json(username_1, aps))
            overall_tp_2 += sum(auth_results)
            overall_total_2 += len(auth_results)
            # print(f'user: {username_1}, auth response: {auth_results[-1]}')

        auth_results = []
        for auth in user_1_auth:
            username_7 = user_name + "d3p7"
            aps = auth["aps"]
            auth_results.append(authenticate_json(username_7, aps))
            overall_fp_1 += sum(auth_results)
            overall_total_3 += len(auth_results)
            # print(f'user: {username_7}, auth response: {auth_results[-1]}')

        auth_results = []
        for auth in user_7_auth:
            username_1 = user_name + "d3p1"
            aps = auth["aps"]
            auth_results.append(authenticate_json(username_1, aps))
            overall_fp_2 += sum(auth_results)
            overall_total_4 += len(auth_results)
            # print(f'user: {username_1}, auth response: {auth_results[-1]}')
    
    print("Overall True acceptance rate (TAR): {:.2f}%".format((overall_tp_1 + overall_tp_2) / (overall_total_1 + overall_total_2) * 100 if (overall_total_1 + overall_total_2) > 0 else 0))
    print("Overall False acceptance rate (FAR): {:.2f}%".format((overall_fp_1 + overall_fp_2) / (overall_total_3 + overall_total_4) * 100 if (overall_total_3 + overall_total_4) > 0 else 0))

