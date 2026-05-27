import json
import os
import re


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


def take_average_scan(aps):
    bssid_dict = {}
    for scan in aps:
        for ap in scan:
            bssid = ap['bssid']
            rssi = ap['rssi']
            if bssid in bssid_dict:
                bssid_dict[bssid].append(rssi)
            else:
                bssid_dict[bssid] = [rssi]
    # average
    avg_scan = []
    for bssid, rssi_list in bssid_dict.items():
        avg_rssi = sum(rssi_list) / len(rssi_list)
        avg_scan.append({'bssid': bssid, 'rssi': avg_rssi})
    return avg_scan


# def loc_take_total_aps(session_list):
#     bssid_set = set()
#     for aps in session_list:
#         for scan in aps:
#             for ap in scan:
#                 bssid_set.add(ap['bssid'])
#     print(f'all aps in this location: {len(bssid_set)}')
def loc_take_total_aps(session_list):
    bssid_set = {ap["bssid"] for aps in session_list for scan in aps for ap in scan}
    print(f"all aps in this location: {len(bssid_set)}")
    # for i in bssid_set:
    #     print(i)


def avg_of_sessions(session_list):
    session_count_list = []
    for aps in session_list:
        bssid_set = {ap["bssid"] for scan in aps for ap in scan}
        session_count_list.append(len(bssid_set))
    print(f'location session with min count {min(session_count_list)}')
    print(f'location session with max count {max(session_count_list)}')
    
    avg = sum(session_count_list) / len(session_count_list)
    print(f'location avg bssid count of sessions: {avg}')

    variance = sum((x - avg) ** 2 for x in session_count_list) / len(session_count_list)
    print(f'location bssid count variance of sessions: {variance}')

    std = variance ** 0.5
    print(f'location bssid count std of sessions: {std}')


def inter_bssid_sessions(session_list):
    session_sets = [
        {ap["bssid"] for scan in aps for ap in scan}
        for aps in session_list
    ]
    inter_set = set.intersection(*session_sets) if session_sets else set()
    print(f'all sessions intersection bssid count: {len(inter_set)}')
    return inter_set


def rssi_fluctuation_cross_sessions(session_list):
    """
    For a location (sessions), find BSSIDs observable in all sessions.
    For each BSSID, collect all RSSI values from the 5 sessions,
    then compute fluctuation as max(rssi) - min(rssi).
    """
    if not session_list:
        print("empty session list")
        return None

    session_sets = [
        {ap["bssid"] for scan in aps for ap in scan}
        for aps in session_list
    ]
    inter_set = set.intersection(*session_sets) if session_sets else set()
    if not inter_set:
        print("no intersection bssid across sessions")
        return None

    fluctuation = {}
    for bssid in inter_set:
        rssi_list = [
            ap["rssi"]
            for aps in session_list
            for scan in aps
            for ap in scan
            if ap["bssid"] == bssid
        ]
        if not rssi_list:
            continue
        fluctuation[bssid] = max(rssi_list) - min(rssi_list)

    if not fluctuation:
        print("no valid bssid fluctuation computed")
        return None

    max_bssid = max(fluctuation, key=fluctuation.get)
    min_bssid = min(fluctuation, key=fluctuation.get)

    print(f"intersection bssid count: {len(inter_set)}")
    print(f"max rssi fluctuation bssid: {max_bssid} ({fluctuation[max_bssid]:.2f})")
    print(f"min rssi fluctuation bssid: {min_bssid} ({fluctuation[min_bssid]:.2f})")

    return {
        "intersection": inter_set,
        "fluctuation": fluctuation,
        "max": (max_bssid, fluctuation[max_bssid]),
        "min": (min_bssid, fluctuation[min_bssid]),
    }


            




# this is use to compare same bssid's strength in different scan

if __name__ == "__main__":

    log_dir = "../log_auth_distance"
    auth_file = "auth_app_20250707_161418_d1p1.log"

    auth_file_path = os.path.join(log_dir, auth_file)
    auth_json_list = extract_JSON_from_log(auth_file_path)

    username_list = ['t0d1p1', 't1d1p1', 't2d1p1', 't3d1p1', 't4d1p1']
    for u in username_list:
        print(f'user: {u}=======================' )
        session_list = []
        for auth_json in auth_json_list:
            if auth_json['username'] == u:
                # aps are 20 scans
                aps = auth_json['aps']
                session_list.append(aps)
        # take aps total num
        print(len(session_list))
        loc_take_total_aps(session_list)
        # take avg of these sessions
        # max aps seen in this session
        # min
        # var
        avg_of_sessions(session_list)
        # inter
        inter_bssid_sessions(session_list)

        # rssi flucutation
        rssi_fluctuation_cross_sessions(session_list)






    # reg_file = "auth_app_moto_reg.log"
    # reg_file_path = os.path.join(log_dir, reg_file)
    # reg_json_list = extract_JSON_from_log(reg_file_path)
    # for reg_json in reg_json_list:
    #     if reg_json['username'] == 'mmoffice':
    #         aps = reg_json['aps']
    #         avg_scan_reg = take_average_scan(aps)

    # auth_file = "auth_app_p7_auth.log"
    # auth_file_path = os.path.join(log_dir, auth_file)
    # auth_json_list = extract_JSON_from_log(auth_file_path)

    # rssi_diff_list = []
    
    # for auth_json in auth_json_list:
    #     if auth_json['username'] == 'mmoffice':
    #         aps = auth_json['aps']
    #         avg_scan_auth = take_average_scan(aps)
    #         # compare: union bssid, and print each rssi
    #         bssid_set = set()
    #         for ap in avg_scan_reg:
    #             bssid_set.add(ap['bssid'])
    #         for ap in avg_scan_auth:
    #             bssid_set.add(ap['bssid'])
    #         print(f"Comparing scans for user 'mmoffice':")
    #         for bssid in bssid_set:
    #             rssi_reg = next((ap['rssi'] for ap in avg_scan_reg if ap['bssid'] == bssid), None)
    #             rssi_auth = next((ap['rssi'] for ap in avg_scan_auth if ap['bssid'] == bssid), None)
    #             print(f"BSSID: {bssid} \t Reg RSSI: {rssi_reg} \t Auth RSSI: {rssi_auth}")
    #             if rssi_reg is not None and rssi_auth is not None:
    #                 rssi_diff = abs(rssi_reg - rssi_auth)
    #                 rssi_diff_list.append(rssi_diff)
    #                 print(f"RSSI difference: {rssi_diff}")
    #     print("---------------------")

    # print(f"average rssi difference: {sum(rssi_diff_list)/len(rssi_diff_list)}")
    # print(f"max rssi difference: {max(rssi_diff_list)}")
    # print(f"min rssi difference: {min(rssi_diff_list)}")


    
