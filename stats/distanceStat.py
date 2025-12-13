import glob
import re
import json


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

    # # log_file_1 = "../log_auth_distance/auth_app_20250707_161418_d1p1.log"
    # # log_file_1 = "../log_auth_distance_sigma1/auth_app_20250922_123905_d1p1.log"
    # log_file_1 = "../log_auth_distance_sigma2/auth_app_20250923_102547_d1p1.log"
    # json_1 = extract_JSON_from_log(log_file_1)
    # tp1, total1 = stat_auth_result("p1", "p1", json_1)

    # # log_file_2 = "../log_auth_distance/auth_app_20250708_010914_d1p2_d1p12.log"
    # # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_124157_d1p2_d1p12.log"
    # log_file_2 = "../log_auth_distance_sigma2/auth_app_20250923_103010_d1p2_d1p12.log"
    # json_2 = extract_JSON_from_log(log_file_2)
    # json_2_1 = json_2[0:25]
    # tp2, total2 = stat_auth_result("p2", "p2", json_2_1)
    # json_2_2 = json_2[25:50]
    # fp1, total3 = stat_auth_result("p2", "p1", json_2_2)
    # json_2_3 = json_2[50:75]
    # fp2, total4 = stat_auth_result("p1", "p2", json_2_3)
    # print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    # print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))


    # print("\n\n")
    # #
    # # log_file_1 = "../log_auth_distance/auth_app_20250707_171219_d2p2.log"
    # # log_file_1 = "../log_auth_distance_sigma1/auth_app_20250922_132211_d2p2.log"
    # log_file_1 = "../log_auth_distance_sigma2/auth_app_20250923_104535_d2p2.log"
    # json_1 = extract_JSON_from_log(log_file_1)
    # tp1, total1 = stat_auth_result("p2", "p2", json_1)

    # # log_file_2 = "../log_auth_distance/auth_app_20250708_012816_d2p3_d2p23.log"
    # # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_132403_d2p3_d2p23.log"
    # log_file_2 = "../log_auth_distance_sigma2/auth_app_20250923_104751_d2p3_d2p23.log"
    # json_2 = extract_JSON_from_log(log_file_2)
    # json_2_1 = json_2[0:25]
    # tp2, total2 = stat_auth_result("p3", "p3", json_2_1)
    # json_2_2 = json_2[25:50]
    # fp1, total3 = stat_auth_result("p3", "p2", json_2_2)
    # json_2_3 = json_2[50:75]
    # fp2, total4 = stat_auth_result("p2", "p3", json_2_3)
    # print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    # print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))


    # log_dir = "../log_auth_distance_less_alpha13"
    # log_dir = "../log_auth_simple_mlp"
    
    # log_dir = "../log_auth_fingerprint_simpleCNN" # with random shuffle in training
    # log_dir = "../log_auth_gnnmaxpool_randomtrain" # with random shuffle in training

    log_dir = "../log_auth_gnnmeanpool_randomtrain" # with random shuffle in training, (our best result)
    # log_dir = "../log_auth_comparison_NFE"
    # log_dir = "../log_auth_nov6_sigma10"
    log_dir = "../log_auth_nov6_sigma30"

    log_files = glob.glob(f"{log_dir}/*")
    log_files.sort()

    print("\n\n")
    #
    # log_file_1 = "../log_auth_distance/auth_app_20250707_180733_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma1/auth_app_20250922_133317_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma2/auth_app_20250923_120731_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma2_norm/auth_app_20251010_185353_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192244_d3p3.log"
    # log_file_1 = glob.glob(f"{log_dir}/*d3p3.log")[0]
    log_file_1 = log_files[0]
    json_1 = extract_JSON_from_log(log_file_1)
    tp1, total1 = stat_auth_result("p3", "p3", json_1)

    # log_file_2 = "../log_auth_distance/auth_app_20250708_013841_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_133633_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma2/auth_app_20250923_120913_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma2_norm/auth_app_20251010_191910_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192420_d3p1_d3p31.log"
    # log_file_2 = glob.glob(f"{log_dir}/*d3p1_d3p31.log")[0]
    log_file_2 = log_files[1]
    json_2 = extract_JSON_from_log(log_file_2)
    json_2_1 = json_2[0:25]
    tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
    json_2_2 = json_2[25:50]
    fp1, total3 = stat_auth_result("p1", "p3", json_2_2)
    json_2_3 = json_2[50:75]
    fp2, total4 = stat_auth_result("p3", "p1", json_2_3)
    print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))



    print("\n\n")
    #
    # log_file_1 = "../log_auth_distance/auth_app_20250707_180733_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma1/auth_app_20250922_133317_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma2/auth_app_20250928_132609_d5p5.log"
    # log_file_1 = "../log_auth_distance_sigma2_norm/auth_app_20251010_192349_d5p5.log"
    # log_file_1 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192545_d5p5.log"
    # log_file_1 = glob.glob(f"{log_dir}/*d5p5.log")[0]
    log_file_1 = log_files[2]
    json_1 = extract_JSON_from_log(log_file_1)
    tp1, total1 = stat_auth_result("p5", "p5", json_1)

    # log_file_2 = "../log_auth_distance/auth_app_20250708_013841_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_133633_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma2/auth_app_20250928_143214_d5p1_d5p51.log"
    # log_file_2 = "../log_auth_distance_sigma2_norm/auth_app_20251010_192530_d5p1_d5p51.log"
    # log_file_2 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192732_d5p1_d5p51.log"
    # log_file_2 = glob.glob(f"{log_dir}/*d5p1_d5p51.log")[0]
    log_file_2 = log_files[3]
    json_2 = extract_JSON_from_log(log_file_2)
    json_2_1 = json_2[0:25]
    tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
    json_2_2 = json_2[25:50]
    fp1, total3 = stat_auth_result("p1", "p5", json_2_2)
    json_2_3 = json_2[50:75]
    fp2, total4 = stat_auth_result("p5", "p1", json_2_3)
    print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))


    print("\n\n")
    #
    # log_file_1 = "../log_auth_distance/auth_app_20250707_180733_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma1/auth_app_20250922_133317_d3p3.log"
    # log_file_1 = "../log_auth_distance_sigma2/auth_app_20251005_194145_d7p7.log"
    # log_file_1 = "../log_auth_distance_sigma2_norm/auth_app_20251010_192744_d7p7.log"
    # log_file_1 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_192905_d7p7.log"
    # log_file_1 = glob.glob(f"{log_dir}/*d7p7.log")[0]
    log_file_1 = log_files[4]
    json_1 = extract_JSON_from_log(log_file_1)
    tp1, total1 = stat_auth_result("p7", "p7", json_1)

    # log_file_2 = "../log_auth_distance/auth_app_20250708_013841_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma1/auth_app_20250922_133633_d3p1_d3p31.log"
    # log_file_2 = "../log_auth_distance_sigma2/auth_app_20251006_111030_d7p1_d7p71.log"
    # log_file_2 = "../log_auth_distance_sigma2_norm/auth_app_20251010_193054_d7p1_d7p71.log"
    # log_file_2 = "../log_auth_distance_sigma2_norm_hn/auth_app_20251014_193011_d7p1_d7p71.log"
    # log_file_2 = glob.glob(f"{log_dir}/*d7p1_d7p71.log")[0]
    log_file_2 = log_files[5]
    json_2 = extract_JSON_from_log(log_file_2)
    json_2_1 = json_2[0:25]
    tp2, total2 = stat_auth_result("p1", "p1", json_2_1)
    json_2_2 = json_2[25:50]
    fp1, total3 = stat_auth_result("p1", "p7", json_2_2)
    json_2_3 = json_2[50:75]
    fp2, total4 = stat_auth_result("p7", "p1", json_2_3)
    print("Overall True acceptance rate (TAR): {:.2f}%".format((tp1 + tp2) / (total1 + total2) * 100 if (total1 + total2) > 0 else 0))
    print("Overall False acceptance rate (FAR): {:.2f}%".format((fp1 + fp2) / (total3 + total4) * 100 if (total3 + total4) > 0 else 0))
