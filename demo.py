# import torch
# from torch_geometric.data import Data

# from torch_geometric.nn import GCNConv, global_mean_pool


# # test if MPS is available
# if torch.backends.mps.is_available():
#     mps_device = torch.device("mps")

#     edge_index = torch.tensor([[0, 1, 1, 2],
#                            [1, 0, 2, 1]], dtype=torch.long,
#                            device=mps_device)
#     x = torch.tensor([[-1], [0], [1]], dtype=torch.float, device=mps_device)
#     print (x.device)

#     data = Data(x=x, edge_index=edge_index)

#     print (data)

# else:
#     print ("MPS device not found.")
# # result: we dont use MPS to train because it is slow on PyG

import numpy as np

def closest_positive_point_vec(x: np.ndarray, r: np.ndarray) -> np.ndarray:
    """
    对向量 x 和向量 r（或标量 r）逐元素计算：
      p_i = x_i mod r_i，如果 p_i == 0 则取 r_i
    返回每个维度上最小的正整数代表元向量 p。
    """
    # 1) 计算逐元素同余
    p = np.mod(x, r)
    # 2) 对于同余结果中等于 0 的位置，用对应的 r 值替代
    p = np.where(p == 0, r, p)
    return p

# # 示例 1：r 为向量
# x = np.array([ 7, -4,  2, -10])
# r = np.array([ 3,  5,  4,   3])
# # 预期输出： [1, 1, 2, 2]
# print(closest_positive_point_vec(x, r))

# # 示例 2：r 为标量，NumPy 会自动广播
# x = np.array([ 7, -4,  2, -10])
# r = 3
# # 预期输出： [1, 2, 2, 2]
# print(closest_positive_point_vec(x, r))


from typing import Union, Tuple

def get_lattice_cell(
    v: np.ndarray,
    x: np.ndarray,
    r: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    v = np.asarray(v, dtype=float)
    x = np.asarray(x, dtype=float)
    r = np.asarray(r, dtype=float)
    k = np.floor((v - x) / (2 * r) + 0.5).astype(int)
    # k = np.floor((v - x) / (2 * r) - 0.5).astype(int)
    c_k = x + 2 * k * r
    return k, c_k


import json

if __name__ == "__main__":

    # x = np.array([1, 1])
    # r = np.array([2, 3])
    # v = np.array([4.1, 5.9])
    # k, ck = get_lattice_cell(v, x, r)
    # print("\ntest 1\nk:", k, "\nck:", ck)
    # # ck: 5, 7

    # v = np.array([1.1, 1.9])
    # k, ck = get_lattice_cell(v, x, r)
    # print("\ntest 2-1\nk:", k, "\nck:", ck)
    # # ck: 1, 1

    # v = np.array([-0.1, -1.1])
    # k, ck = get_lattice_cell(v, x, r)
    # print("\ntest 2-2\nk:", k, "\nck:", ck)
    # # ck: 1, 1

    # v = np.array([-4.1, -7.1])
    # k, ck = get_lattice_cell(v, x, r)
    # print("\ntest 3\nk:", k, "\nck:", ck)
    # # ck: -3, -5

    empty_json_file = "/Users/noname/mlprojects/gnn_demo/betterdata/2025-06-16+10:51:46lounge.json"
    # empty_json_file = "/Users/noname/mlprojects/gnn_demo/betterdata/2025-06-16+10:54:02lounge.json"
    with open(empty_json_file, 'r') as f:
        data = json.load(f)
        if not data:
            print("Empty JSON file detected.")
        else:
            print(data)
