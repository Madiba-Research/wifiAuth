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

    # log_file = "../log_auth_25user/auth_app_20251118_190305.log"  # sigma = 2
    # log_file = "../log_auth_25user_15/auth_app_20251118_234454.log"  # sigma = 1.5
    # log_file = "../log_auth_25user_12/auth_app_20251118_235525.log" # sigma = 1.2, our best


    log_file = "../log_auth_25u_nfe_0045/auth_app_20251119_200847.log"
    # Final Overall True acceptance rate (TAR): 56.32%, 1 - FAR: 43.68%
    # Final Overall False acceptance rate (FAR): 51.05%

    # log_file = "../log_auth_25u_nfe_0035/auth_app_20251119_200206.log"
    # scale = 0.035
    # Final Overall True acceptance rate (TAR): 74.21%, 1 - FAR: 25.79%
    # Final Overall False acceptance rate (FAR): 59.47%

    # log_file = "../log_auth_25u_nfe/auth_app_20251119_114810.log"
    # scale = 0.025
    # Final Overall True acceptance rate (TAR): 89.47%, 1 - FAR: 10.53%
    # Final Overall False acceptance rate (FAR): 81.58%

    # log_file = "../log_auth_25u_nfe_001/auth_app_20251119_195409.log"
    # scale = 0.01
    # Final Overall True acceptance rate (TAR): 94.74%, 1 - FAR: 5.26%
    # Final Overall False acceptance rate (FAR): 91.05%


    
    # for threshold

    # log_file = "../log_auth_25u_09/auth_app_20251119_190358.log"
    # Final Overall True acceptance rate (TAR): 87.89%, 1 - FAR: 12.11%
    # Final Overall False acceptance rate (FAR): 5.79%

    # log_file = "../log_auth_25u_10/auth_app_20251119_183343.log"
    # Final Overall True acceptance rate (TAR): 91.58%, 1 - FAR: 8.42%
    # Final Overall False acceptance rate (FAR): 6.84%

    # log_file = "../log_auth_25u_11/auth_app_20251119_001118.log"
    # Final Overall True acceptance rate (TAR): 92.11%, 1 - FAR: 7.89%
    # Final Overall False acceptance rate (FAR): 7.89%

    # log_file = "../log_auth_25u_12/auth_app_20251118_235525.log"
    # Final Overall True acceptance rate (TAR): 95.26%, 1 - FAR: 4.74%
    # Final Overall False acceptance rate (FAR): 7.89%

    # log_file = "../log_auth_25u_13/auth_app_20251119_191030.log"
    # Final Overall True acceptance rate (TAR): 96.32%, 1 - FAR: 3.68%
    # Final Overall False acceptance rate (FAR): 7.89%

    # log_file = "../log_auth_25u_14/auth_app_20251119_184419.log"
    # Final Overall True acceptance rate (TAR): 97.37%, 1 - FAR: 2.63%
    # Final Overall False acceptance rate (FAR): 9.47%


    json_all = extract_JSON_from_log(log_file)

    overall_tp_1 = 0
    overall_total_1 = 0
    overall_tp_2 = 0
    overall_total_2 = 0
    overall_fp_1 = 0
    overall_total_3 = 0
    overall_fp_2 = 0
    overall_total_4 = 0

    # for old sequence format
    json_1 = json_all[0:25]
    tp1, total1 = stat_auth_result("p7", "p7", json_1)
    overall_tp_1 += tp1
    overall_total_1 += total1

    json_2_1 = json_all[25:50]
    tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
    overall_tp_2 += tp2
    overall_total_2 += total2
    json_2_2 = json_all[50:75]
    fp1, total3 = stat_auth_result("p1", "p7", json_2_2)
    overall_fp_1 += fp1
    overall_total_3 += total3
    json_2_3 = json_all[75:100]
    fp2, total4 = stat_auth_result("p7", "p1", json_2_3)
    overall_fp_2 += fp2
    overall_total_4 += total4
    print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))

    # exit()
    for u in range(0, 20):
        # t6, t7, t11, t12, t21
        if u == 0 or u == 1 or u == 5 or u == 6 or u == 15:
            continue
        user_idx = 100 + u * 20
        cur_json = json_all[user_idx : user_idx + 20]
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
        print("Overall True acceptance rate (TAR): {:.2f}%".format((tp_u_1 + tp_u_2) / (total_u_1 + total_u_2) * 100 if (total_u_1 + total_u_2) > 0 else 0))
        print("Overall False acceptance rate (FAR): {:.2f}%".format((fp_u_1 + fp_u_2) / (total_u_3 + total_u_4) * 100 if (total_u_3 + total_u_4) > 0 else 0))

    print("\nFinal Overall True acceptance rate (TAR): {:.2f}%".format((overall_tp_1 + overall_tp_2) / (overall_total_1 + overall_total_2) * 100 if (overall_total_1 + overall_total_2) > 0 else 0))
    print("Final Overall False acceptance rate (FAR): {:.2f}%".format((overall_fp_1 + overall_fp_2) / (overall_total_3 + overall_total_4) * 100 if (overall_total_3 + overall_total_4) > 0 else 0))

    # exit()

    
    # tp1, total1 = stat_auth_result("p3", "p3", json_1)

    # # log_file_2 = "../log_auth_distance/auth_app_20250708_013841_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_133633_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma2/auth_app_20250923_120913_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma2_norm/auth_app_20251010_191910_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192420_d3p1_d3p31.log"
    # # log_file_2 = glob.glob(f"{log_dir}/*d3p1_d3p31.log")[0]
    # log_file_2 = log_files[1]
    # json_2 = extract_JSON_from_log(log_file_2)
    # json_2_1 = json_2[0:25]
    # tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
    # json_2_2 = json_2[25:50]
    # fp1, total3 = stat_auth_result("p1", "p3", json_2_2)
    # json_2_3 = json_2[50:75]
    # fp2, total4 = stat_auth_result("p3", "p1", json_2_3)
    # print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    # print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))



    # print("\n\n")
    # #
    # # log_file_1 = "../log_auth_distance/auth_app_20250707_180733_d3p3.log"
    # # log_file_1 = "../log_auth_distance_sigma1/auth_app_20250922_133317_d3p3.log"
    # # log_file_1 = "../log_auth_distance_sigma2/auth_app_20250928_132609_d5p5.log"
    # # log_file_1 = "../log_auth_distance_sigma2_norm/auth_app_20251010_192349_d5p5.log"
    # # log_file_1 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192545_d5p5.log"
    # # log_file_1 = glob.glob(f"{log_dir}/*d5p5.log")[0]
    # log_file_1 = log_files[2]
    # json_1 = extract_JSON_from_log(log_file_1)
    # tp1, total1 = stat_auth_result("p5", "p5", json_1)

    # # log_file_2 = "../log_auth_distance/auth_app_20250708_013841_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_133633_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma2/auth_app_20250928_143214_d5p1_d5p51.log"
    # # log_file_2 = "../log_auth_distance_sigma2_norm/auth_app_20251010_192530_d5p1_d5p51.log"
    # # log_file_2 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192732_d5p1_d5p51.log"
    # # log_file_2 = glob.glob(f"{log_dir}/*d5p1_d5p51.log")[0]
    # log_file_2 = log_files[3]
    # json_2 = extract_JSON_from_log(log_file_2)
    # json_2_1 = json_2[0:25]
    # tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
    # json_2_2 = json_2[25:50]
    # fp1, total3 = stat_auth_result("p1", "p5", json_2_2)
    # json_2_3 = json_2[50:75]
    # fp2, total4 = stat_auth_result("p5", "p1", json_2_3)
    # print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    # print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))


    # print("\n\n")
    # #
    # # log_file_1 = "../log_auth_distance/auth_app_20250707_180733_d3p3.log"
    # # log_file_1 = "../log_auth_distance_sigma1/auth_app_20250922_133317_d3p3.log"
    # # log_file_1 = "../log_auth_distance_sigma2/auth_app_20251005_194145_d7p7.log"
    # # log_file_1 = "../log_auth_distance_sigma2_norm/auth_app_20251010_192744_d7p7.log"
    # # log_file_1 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192905_d7p7.log"
    # # log_file_1 = glob.glob(f"{log_dir}/*d7p7.log")[0]
    # log_file_1 = log_files[4]
    # json_1 = extract_JSON_from_log(log_file_1)
    # tp1, total1 = stat_auth_result("p7", "p7", json_1)

    # # log_file_2 = "../log_auth_distance/auth_app_20250708_013841_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_133633_d3p1_d3p31.log"
    # # log_file_2 = "../log_auth_distance_sigma2/auth_app_20251006_111030_d7p1_d7p71.log"
    # # log_file_2 = "../log_auth_distance_sigma2_norm/auth_app_20251010_193054_d7p1_d7p71.log"
    # # log_file_2 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_193011_d7p1_d7p71.log"
    # # log_file_2 = glob.glob(f"{log_dir}/*d7p1_d7p71.log")[0]
    # log_file_2 = log_files[5]
    # json_2 = extract_JSON_from_log(log_file_2)
    # json_2_1 = json_2[0:25]
    # tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
    # json_2_2 = json_2[25:50]
    # fp1, total3 = stat_auth_result("p1", "p7", json_2_2)
    # json_2_3 = json_2[50:75]
    # fp2, total4 = stat_auth_result("p7", "p1", json_2_3)
    # print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    # print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))
