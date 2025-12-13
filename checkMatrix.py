import numpy as np




if __name__ == "__main__":

    matrix_file_name = 'H_G_demo_32_dimension.npz'
    dim_num = 32
    # matrix_file_name = 'H_G_demo_8_dimension.npz'

    matrix_data = np.load(matrix_file_name)
    H_norm = matrix_data['H']
    G_norm = matrix_data['G']

    print("Loaded matrix H:")
    # for row in H_norm:
    #     print(row)

    print("Loaded matrix G:")
    # for row in G_norm:
    #     print(row)


    # b = Hx, x = Gb
    v_b_list = [np.eye(dim_num)[:, i:i+1] for i in range(dim_num)]
    v_x_lengths = []
    for v_b in v_b_list:
        v_x = G_norm @ v_b
        v_x_l2_norm = np.linalg.norm(v_x)
        v_x_lengths.append(v_x_l2_norm)
        print("length of v_x:", v_x_l2_norm)

    # v_b_1 = np.array([[1], [0], [0], [0], [0], [0], [0], [0]])
    # v_x = G_norm @ v_b
    # v_x_l2_norm = np.linalg.norm(v_x)
    # print("dim 1 length of v_x:", v_x_l2_norm)

    print("max length of v_x:", max(v_x_lengths))
    print("min length of v_x:", min(v_x_lengths))

    # max length of v_x: 2.9510272812705285
    # min length of v_x: 1.2517879539233665