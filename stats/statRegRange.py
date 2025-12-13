import json
import requests
import os
import re
from glob import glob
import numpy as np


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



if __name__ == "__main__":
    
    REG_DIR = "../log_reg_distance"
    reg_files = glob(f"{REG_DIR}/*.log")
    reg_list = []
    for reg_file in reg_files:
        reg_list.extend(extract_JSON_from_log(reg_file))

    avg_x_s_list = []
    std_x_s_list = []

    for reg in reg_list:
        user_name = reg.get("username")
        x_s = reg.get("x_s")
        # x_s_list.append(x_s)
        np_x_s = []
        for x in x_s:
            np_x = np.array(x, dtype=float)
            np_x_s.append(np_x)
        np_x_s = np.array(np_x_s)
        # print(np_x_s)
        # average
        avg_x_s = np.mean(np_x_s, axis=0)
        avg_x_s_list.append(avg_x_s)
        # two standard deviation
        std_x_s = 2 * np.std(np_x_s, axis=0)
        std_x_s_list.append(std_x_s)
        # print(f"user: {user_name}, avg: {avg_x_s}, 2*std: {std_x_s}")

    avg_x_s_array = np.array(avg_x_s_list)
    max_per_dim = np.max(avg_x_s_array, axis=0)
    min_per_dim = np.min(avg_x_s_array, axis=0)

    print(f"每个维度的最大值: {max_per_dim}")
    print(f"每个维度的最小值: {min_per_dim}")
    print(f"每个维度的范围: {max_per_dim - min_per_dim}")

    std_x_s_array = np.array(std_x_s_list)
    min_std_per_dim = np.min(std_x_s_array, axis=0)
    print(f"每个维度的最小2倍标准差: {min_std_per_dim}")

    



        

    
