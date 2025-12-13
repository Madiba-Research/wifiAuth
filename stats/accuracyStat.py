from glob import glob
import json
import re
import ast

REG_DIR = "../log_reg"
AUTH_DIR = "../log_auth"


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


def check_user_true_auth(user_auth_data: list) -> dict:
    """
    Check if the user has true authentication results.
    """
    if not user_auth_data:
        print("No authentication data found for this user.")
        return

    # get number of true auth results
    true_auth_count = sum(1 for item in user_auth_data if item.get("result") == True)
    false_auth_count = sum(1 for item in user_auth_data if item.get("result") == False)
    print(
        f"User {user_auth_data[0]['username']}:\n"
        f"\033[34m{true_auth_count}\033[0m true authentication results and "
        f"\033[31m{false_auth_count}\033[0m false authentication results.\n"
    )
    match_dict = {}
    for item in user_auth_data:
        if item.get("result") == True:
            match_key = f"{item['username']} with {item['username']} true auth"
            match_dict[match_key] = match_dict.get(match_key, 0) + 1
        else:
            match_key = f"{item['username']} with {item['username']} false auth"
            match_dict[match_key] = match_dict.get(match_key, 0) + 1
    # for key, value in match_dict.items():
    #     print(f"{key}: {value} times")
    return match_dict
    

if __name__ == "__main__":

    total_dict = {}
    # first read matched auth results data
    auth_files = glob(f"{AUTH_DIR}/*.log")
    auth_list = []
    
    for auth_file in auth_files:
        auth_list.extend(extract_JSON_from_log(auth_file))
    # print(f"auth_list length: {len(auth_list)}")

    # first read matched result, for
    user_list = ["t0", "t1", "t2", "t3", "t4"]
    for user in user_list:
        user_auth_data = [item for item in auth_list if item["username"] == user]
        total_dict.update(check_user_true_auth(user_auth_data))

    # then use this user's data to validate the auth result as other users
    response_file = "generatedFNresponse.txt"
    unmatch_dict = {}
    with open(response_file, 'r') as f:
        while True:
            line_user = f.readline()
            if not line_user:
                break
            line_response = f.readline()
            user_match = re.search(r"authenticating (\w+) with (\w+)'s data", line_user)
            user_1 = user_match.group(1)
            user_2 = user_match.group(2)
            
            # print(line_response)
            json_match = re.search(r'({.*})', line_response)
            # print(json_match)
            auth_rst = ast.literal_eval(json_match.group(1))['authenticated']
            # auth_rst = json.loads(json_match.group(1))
            if auth_rst:
                dict_key = f"{user_1} with {user_2} true auth"
                # print(f"{user_1} with {user_2} auth result: {auth_rst}")
            else:
                dict_key = f"{user_1} with {user_2} false auth"
            unmatch_dict[dict_key] = unmatch_dict.get(dict_key, 0) + 1

    total_dict.update(unmatch_dict)

    for key, value in total_dict.items():
        print(f"{key}: {value} times")
        
