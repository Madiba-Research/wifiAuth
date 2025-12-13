import generateMatrix as gm
import numpy as np


def find_nearest_integer_vector(v, H):
    """
    Given a point v in lattice space, find the its closest codeword's corresponding integer vector.
    x = G * b
    b = H * x
    """
    b_syndrome = H @ v
    b = np.round(b_syndrome).astype(int)  # Round to nearest integer
    return b


def generate_cluster_with_center(v, var, n=10):
    return v + np.random.normal(0, var, size=(n, len(v)))


def get_cluster_mean(cluster):
    return np.mean(cluster, axis=0)


def get_cluster_variance(cluster):
    return np.var(cluster, axis=0)


def round_to_radius(diff):
    fractional = diff % 1
    int_part = np.floor(diff)
    return np.where(
        fractional < 0.5,
        int_part + 0.5,
        np.where(fractional == 0.5, diff, np.ceil(diff))
    )


def get_closest_origin_cell_cood(x: np.ndarray, r: np.ndarray) -> np.ndarray:
    p = np.mod(x, 2 * r)
    # p = np.where(p == 0, r, p)
    return p


def get_lattice_cell(
    v: np.ndarray,
    x: np.ndarray,
    r: np.ndarray
) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    x = np.asarray(x, dtype=float)
    r = np.asarray(r, dtype=float)
    k = np.floor((v - x) / (2 * r) + 0.5).astype(int)
    # k = np.floor((v - x) / (2 * r) - 0.5).astype(int)
    c_k = x + 2 * k * r
    return c_k




if __name__ == '__main__':

    # n = 7
    # d = 3
    # h_values = [0.5, 0.8, 1]
    # seed = 42
    
    # load from file
    matrix_file_name = 'H_G_demo_7_dimension.npz'
    matrix_data = np.load(matrix_file_name)
    H_norm = matrix_data['H']
    G_norm = matrix_data['G']

    # test 1:
    # generate a codeword c
    b = np.array([1, 1, 1, 1, 1, 1, 1])
    c = G_norm @ b
    print("\nTest1\nGenerated codeword c:", c)

    # test 2:
    # convert c to integer vector
    b_recovered = find_nearest_integer_vector(c, H_norm)
    print("\nTest2\nRecovered integer vector b from codeword c:", b_recovered)

    # test 3:
    # add noise to c, and check if we can recover back to b
    np.random.seed(42)
    w = np.random.normal(0, 0.1, size=c.shape)  # Add Gaussian noise
    x = c + w
    print("\nTest3\nNoisy codeword x:", x)
    b_recovered_noisy = find_nearest_integer_vector(x, H_norm)
    print("Recovered integer vector b from noisy codeword x:", b_recovered_noisy)

    # test 4-1:
    # simulate registration with a cluster around x
    # xs_reg = generate_cluster_with_center(x, 0.1, 10)
    xs_reg = generate_cluster_with_center(x, 0.2, 10)
    print("\nTest4-1\nGenerate clusters around codeword x:")
    # for i, x in enumerate(xs_reg):
    #     print(f"Cluster point {i}: {x}")
    x_mean = get_cluster_mean(xs_reg)
    print("Mean of cluster points:", x_mean)
    # x_var = get_cluster_variance(xs_reg)
    # print("Variance of cluster points:", x_var)
    # get corresponding b, and codeword c
    b_reg = find_nearest_integer_vector(x_mean, H_norm)
    c_reg = G_norm @ b_reg
    print("Recovered integer vector b from cluster mean:", b_reg)
    print("Corresponding codeword c from cluster mean:", c_reg)
    d = c_reg - x_mean
    print("Difference between recovered codeword and cluster mean:", d)
    # next scale the distribution feature (variance) in b's integer space
    # b_reg_var = H_norm @ x_var @ H_norm.T
    # print("Variance of recovered integer vector b from cluster mean:", b_reg_var)
    
    # test 4-2
    # get the valid range in b's integer space
    '''
    cs_reg = xs_reg - c_reg
    cs_reg => bs_reg
    find radius between bs_reg and b_reg
    '''
    print("\nTest4-2")
    cs_reg = xs_reg + d
    # for i, c_w in enumerate(cs_reg):
    #     b_w = H_norm @ c_w
    #     print(f"Cluster point {i} in integer space: {b_w}")
    mapped_b_w = cs_reg @ H_norm.T
    # print("Mapped cluster points in integer space:", mapped_b_w)
    b_diff = np.abs(mapped_b_w - b_reg)
    # print("Difference between mapped cluster points and recovered b:", b_diff)
    b_radius = np.max(b_diff, axis=0)
    print("Radius in integer space:", b_radius)
    b_radius_int = round_to_radius(b_radius)
    print("Radius in integer space rounded:", b_radius_int)

    # test 4-3
    # based on the radius in integer space, slice the integer space into grid
    print("\nTest4-3")
    # round the radius the nearest upper bound integer
    # b_radius_int = np.ceil(b_radius).astype(int)
    b_cell = get_closest_origin_cell_cood(b_reg, b_radius_int)
    print("Closest origin cell coordinates in integer space:", b_cell)

    # Authentication simulation
    print("\nAuthentication Simulation")
    # generate an in-range point of b
    print("\nTest5-1")
    for i, b_w in enumerate(mapped_b_w):
        print(f"Cluster point {i} in integer space: {b_w}")
        b_w_cell = get_lattice_cell(b_w, b_cell, b_radius_int)
        print(f"Cluster point {i} in lattice cell coordinates: {b_w_cell}")
    # generate an out-range point of b
    print("\nTest5-2")
    b_w_false = mapped_b_w + np.random.normal(0, 0.5, size=mapped_b_w.shape)  # Add noise to create false points
    for i, b_w_f in enumerate(b_w_false):
        print(f"False cluster point {i} in integer space: {b_w_f}")
        b_w_f_cell = get_lattice_cell(b_w_f, b_cell, b_radius_int)
        print(f"False cluster point {i} in lattice cell coordinates: {b_w_f_cell}")
    
    


