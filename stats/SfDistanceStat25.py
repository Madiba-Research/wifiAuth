import glob
import re
import json
from typing import Final


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


def stat_auth_result(data_user_p, auth_user_p, json_list: list):

    # ANSI color codes
    GREEN = "\033[92m"
    ORANGE = "\033[33m"   # Orange is not standard; use yellow instead
    RESET = "\033[0m"

    user_set = set([item['username'] for item in json_list if item.get('username')])

    total_len = 0
    total_true = 0

    # print(user_set)
    for auth_user in user_set:
        data_user = auth_user.replace(auth_user_p, data_user_p)

        # Choose color
        if auth_user == data_user:
            color = GREEN
        else:
            color = ORANGE

        # Color the user display
        colored_auth_user = f"{color}{auth_user}{RESET}"

        auth_user_json = [item for item in json_list if item.get('username') == auth_user]
        len_true = sum(1 for item in auth_user_json if item.get('result') == True)
        len_false = sum(1 for item in auth_user_json if item.get('result') == False)
        print(f"Auth ({colored_auth_user}) with data ({data_user}): ({len_true}) pass and ({len_false}) fails.")

        total_len += (len_true + len_false)
        total_true += len_true
        
    if auth_user_p == data_user_p:
        print("True acceptance rate (TAR): {:.2f}%".format((total_true / total_len) * 100 if total_len > 0 else 0))
    else:
        print("False acceptance rate (FAR): {:.2f}%".format((total_true / total_len) * 100 if total_len > 0 else 0))

    return total_true, total_len




if __name__ == "__main__":


    log_file = "../log_auth_sf_test/auth_app_20251204_141649.log"

    tar_list = []
    far_list = []


    json_all = extract_JSON_from_log(log_file)

    for ssf in range(100, 200, 1):

        print("\nStat for scale factor:", ssf / 100.0)

        s_postfix = 's' + str(ssf / 100.0).replace('.', '_')
        json_all_sf = [item for item in json_all if item.get('username', '').endswith(s_postfix)]

        overall_tp_1 = 0
        overall_total_1 = 0
        overall_tp_2 = 0
        overall_total_2 = 0
        overall_fp_1 = 0
        overall_total_3 = 0
        overall_fp_2 = 0
        overall_total_4 = 0

        # for old sequence format
        json_1 = json_all_sf[0:25]
        tp1, total1 = stat_auth_result("p7", "p7", json_1)
        overall_tp_1 += tp1
        overall_total_1 += total1

        json_2_1 = json_all_sf[25:50]
        tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
        overall_tp_2 += tp2
        overall_total_2 += total2
        json_2_2 = json_all_sf[50:75]
        fp1, total3 = stat_auth_result("p1", "p7", json_2_2)
        overall_fp_1 += fp1
        overall_total_3 += total3
        json_2_3 = json_all_sf[75:100]
        fp2, total4 = stat_auth_result("p7", "p1", json_2_3)
        overall_fp_2 += fp2
        overall_total_4 += total4
        # print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
        # print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))

        # exit()
        for u in range(0, 20):
            # t6, t7, t11, t12, t21
            if u == 0 or u == 1 or u == 5 or u == 6 or u == 15:
                continue
            
            user_idx = 100 + u * 20
            cur_json = json_all_sf[user_idx : user_idx + 20]
            tp_u_1, total_u_1 = stat_auth_result("p7", "p7", cur_json[0:5])
            overall_tp_1 += tp_u_1
            overall_total_1 += total_u_1
            tp_u_2, total_u_2 = stat_auth_result("p1", "p1", cur_json[5:10])
            overall_tp_2 += tp_u_2
            overall_total_2 += total_u_2
            fp_u_1, total_u_3 = stat_auth_result("p1", "p7", cur_json[10:15])
            overall_fp_1 += fp_u_1
            overall_total_3 += total_u_3
            fp_u_2, total_u_4 = stat_auth_result("p7", "p1", cur_json[15:20])
            overall_fp_2 += fp_u_2
            overall_total_4 += total_u_4
            # print("Overall True acceptance rate (TAR): {:.2f}%".format((tp_u_1 + tp_u_2) / (total_u_1 + total_u_2) * 100 if (total_u_1 + total_u_2) > 0 else 0))
            # print("Overall False acceptance rate (FAR): {:.2f}%".format((fp_u_1 + fp_u_2) / (total_u_3 + total_u_4) * 100 if (total_u_3 + total_u_4) > 0 else 0))

        print("\nFinal Overall True acceptance rate (TAR): {:.2f}%".format((overall_tp_1 + overall_tp_2) / (overall_total_1 + overall_total_2) * 100 if (overall_total_1 + overall_total_2) > 0 else 0))
        print("Final Overall False acceptance rate (FAR): {:.2f}%".format((overall_fp_1 + overall_fp_2) / (overall_total_3 + overall_total_4) * 100 if (overall_total_3 + overall_total_4) > 0 else 0))

        tar_list.append((overall_tp_1 + overall_tp_2) / (overall_total_1 + overall_total_2) * 100 if (overall_total_1 + overall_total_2) > 0 else 0)
        far_list.append((overall_fp_1 + overall_fp_2) / (overall_total_3 + overall_total_4) * 100 if (overall_total_3 + overall_total_4) > 0 else 0)

    with open("sf25user_tar_far_stat.txt", "w") as f:
        f.write("Scale Factor\tTAR (%)\tFAR (%)\n")
        for i in range(len(tar_list)):
            scale_factor = 1.0 + i * 0.2
            f.write(f"{scale_factor:.1f}\t{tar_list[i]:.2f}\t{far_list[i]:.2f}\n")
    