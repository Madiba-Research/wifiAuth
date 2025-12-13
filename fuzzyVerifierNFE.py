from user import User
import numpy as np
# from ldlcDecodedemo import LDLCDecoder
from ldlcDecodeDemo1 import LDLCDecoder


def get_cluster_mean(cluster):
    return np.mean(cluster, axis=0)


def find_nearest_integer_vector(v, H):
    """
    Given a point v in lattice space, find the its closest codeword's corresponding integer vector.
    x = G * b
    b = H * x
    """
    b_syndrome = H @ v
    b = np.round(b_syndrome).astype(int)  # Round to nearest integer
    return b


def round_to_radius(diff):
    """
    Round the diff to the nearest valid radius for each dimension.
    If the fractional part is less than or equal to 0.5, round up to the 0.5,
    if it is over 0.5, round up to the next integer.
    """
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
    """
    Given a point v in integer space, and the cell definition x and radius r,
    return the coordinate of the cell that v belongs to.
    """
    v = np.asarray(v, dtype=float)
    x = np.asarray(x, dtype=float)
    r = np.asarray(r, dtype=float)
    k = np.floor((v - x) / (2 * r) + 0.5).astype(int)
    # c_k as the k-th cell's coordinate
    c_k = x + 2 * k * r
    return c_k




class NeuralFuzzyVerifier:

    def __init__(self, matrix_file_name: str):
        # load the configuration for lattice space defnition: H and G matrices
        matrix_data = np.load(matrix_file_name)
        self.H_norm = matrix_data['H']
        self.G_norm = matrix_data['G']
        sigma2 = 1 / (2.0 * np.pi * np.e)
        self.ldlc_decoder = LDLCDecoder(self.H_norm, sigma2=sigma2, resolution= 1/16, pdf_range=10)


    def sim_register(self, x_s):
        """
        Simulate a registration, for checking b space data, r_b and O_b
        This does not write user info into database.
        """
        x_mean = get_cluster_mean(x_s)
        # print("Mean of cluster points:", x_mean) # make it as log in future work
        b_reg = find_nearest_integer_vector(x_mean, self.H_norm)
        # lattice space codeword
        c_reg = self.G_norm @ b_reg
        d = c_reg - x_mean

        # user's specified parameter learn
        c_s = x_s + d
        b_s = c_s @ self.H_norm.T
        b_diff = np.abs(b_s - b_reg)
        b_radius = np.max(b_diff, axis=0)
        # print("b_radius:", b_radius, "\nb_reg:", b_reg)
        # print(b_reg[0])
        # print(b_radius[1])
        # print("\n")

        x_mean = get_cluster_mean(x_s)
        b_mean = self.H_norm @ x_mean
        print(b_mean[7])
        
    

    def register(self, user: User, x_s, scale_a: float):
        """
        Register a user with its provided vectors for registration x_s.
        It extracts the user's valid codeword, but also learns the user's base cell and acceptable valid radius.
        """
        x_s_scaled  = x_s * scale_a
        x_mean = get_cluster_mean(x_s_scaled)
        print("Mean of cluster points:", x_mean) # make it as log in future work

        b_hat, _x_hat = self.ldlc_decoder.decode(x_mean, max_iterations=10, verbose=False)
        x_hat = self.G_norm @ b_hat
        d = x_hat - x_mean

        b_rad_zero = np.zeros_like(b_hat)
        b_base_zero = np.zeros_like(b_hat)

        print("Registered b_hat:", b_hat)
        print("Registered x_hat:", x_hat)

        user.set_auth_data(d, b_rad_zero, b_base_zero, x_mean)

        # # ==========


        # b_reg = find_nearest_integer_vector(x_mean, self.H_norm)
        # # lattice space codeword
        # c_reg = self.G_norm @ b_reg
        # d = c_reg - x_mean

        # # user's specified parameter learn
        # c_s = x_s + d
        # b_s = c_s @ self.H_norm.T
        
        # # original radius generation method, accepting all collected samples
        # if sigma <= 0:
        #     b_diff = np.abs(b_s - b_reg)
        #     b_radius = np.max(b_diff, axis=0)
        # else:
        #     # filter out, generate b_radius with standard deviation
        #     std_b = np.std(b_s, axis=0)
        #     b_radius = std_b * sigma

        # b_radius_int = round_to_radius(b_radius)
        # # O_reg in paper's representation
        # b_cell = get_closest_origin_cell_cood(b_reg, b_radius_int)

        # # recall we set x_mean as the user's password, this should be hashed in future work
        # user.set_auth_data(d, b_radius_int, b_cell, x_mean)


    def authenticate_calc(self, user: User, y, scale_a: float):
        # print("Authenticating user:", user)
        # print(y)
        """
        Authenticate a user with the provided vector y.
        """
        # c_a = y + user.user_dist
        # b_a = c_a @ self.H_norm.T
        # b_a_celled = get_lattice_cell(b_a, user.user_base, user.user_rad)
        # c_a = self.G_norm @ b_a_celled
        # x_a = c_a - user.user_dist

        y_scaled = y * scale_a
        y_placed = y_scaled + user.user_dist
        b_a_hat, _y_hat = self.ldlc_decoder.decode(y_placed, max_iterations=10, verbose=False)
        # x_a = y_hat - user.user_dist
        y_hat = self.G_norm @ b_a_hat
        x_a = y_hat - user.user_dist

        print("b_a_hat:", b_a_hat)
        print("y_hat:", y_hat)

        # check if the recovered x_a matches the user's password
        # return np.allclose(x_a, user.user_passwd, atol=1e-5)
        return x_a
        

