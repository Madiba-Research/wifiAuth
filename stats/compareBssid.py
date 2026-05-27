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



# this is use to compare same bssid's strength in different scan

if __name__ == "__main__":

    log_dir = "../authFromPixel7"

    reg_file = "auth_app_moto_reg.log"
    reg_file_path = os.path.join(log_dir, reg_file)
    reg_json_list = extract_JSON_from_log(reg_file_path)
    for reg_json in reg_json_list:
        if reg_json['username'] == 'mmoffice':
            aps = reg_json['aps']
            avg_scan_reg = take_average_scan(aps)

    auth_file = "auth_app_p7_auth.log"
    auth_file_path = os.path.join(log_dir, auth_file)
    auth_json_list = extract_JSON_from_log(auth_file_path)

    rssi_diff_list = []
    
    for auth_json in auth_json_list:
        if auth_json['username'] == 'mmoffice':
            aps = auth_json['aps']
            avg_scan_auth = take_average_scan(aps)
            # compare: union bssid, and print each rssi
            bssid_set = set()
            for ap in avg_scan_reg:
                bssid_set.add(ap['bssid'])
            for ap in avg_scan_auth:
                bssid_set.add(ap['bssid'])
            print(f"Comparing scans for user 'mmoffice':")
            for bssid in bssid_set:
                rssi_reg = next((ap['rssi'] for ap in avg_scan_reg if ap['bssid'] == bssid), None)
                rssi_auth = next((ap['rssi'] for ap in avg_scan_auth if ap['bssid'] == bssid), None)
                print(f"BSSID: {bssid} \t Reg RSSI: {rssi_reg} \t Auth RSSI: {rssi_auth}")
                if rssi_reg is not None and rssi_auth is not None:
                    rssi_diff = abs(rssi_reg - rssi_auth)
                    rssi_diff_list.append(rssi_diff)
                    print(f"RSSI difference: {rssi_diff}")
        print("---------------------")

    print(f"average rssi difference: {sum(rssi_diff_list)/len(rssi_diff_list)}")
    print(f"max rssi difference: {max(rssi_diff_list)}")
    print(f"min rssi difference: {min(rssi_diff_list)}")


    