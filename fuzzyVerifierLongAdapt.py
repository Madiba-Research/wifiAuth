from user import User
import numpy as np


def get_cluster_mean(cluster):
    return np.mean(cluster, axis=0)


def ensure_2d_array(values):
    values = np.asarray(values, dtype=float)
    if values.ndim == 1:
        return values.reshape(1, -1)
    return values


def find_nearest_integer_vector(v, H):
    """
    Given a point v in lattice space, find its closest codeword's
    corresponding integer vector.
    """
    b_syndrome = H @ v
    b = np.round(b_syndrome).astype(int)
    return b


def round_to_radius(diff):
    """
    Round the diff to the nearest valid radius for each dimension.
    """
    fractional = diff % 1
    int_part = np.floor(diff)
    return np.where(
        fractional < 0.5,
        int_part + 0.5,
        np.where(fractional == 0.5, diff, np.ceil(diff))
    )


def get_closest_origin_cell_cood(x: np.ndarray, r: np.ndarray) -> np.ndarray:
    return np.mod(x, 2 * r)


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
    return x + 2 * k * r


class RadiusAdaptedFuzzyVerifier:

    def __init__(self, matrix_file_name: str):
        matrix_data = np.load(matrix_file_name)
        self.H_norm = matrix_data["H"]
        self.G_norm = matrix_data["G"]

    def sim_register(self, x_s):
        x_s = ensure_2d_array(x_s)
        x_mean = get_cluster_mean(x_s)
        b_reg = find_nearest_integer_vector(x_mean, self.H_norm)
        c_reg = self.G_norm @ b_reg
        d = c_reg - x_mean
        c_s = x_s + d
        b_s = c_s @ self.H_norm.T
        b_diff = np.abs(b_s - b_reg)
        b_radius = np.max(b_diff, axis=0)
        return {
            "x_mean": x_mean,
            "b_reg": b_reg,
            "dist": d,
            "radius": round_to_radius(b_radius),
        }

    def range_estimation(self, b_s, sigma: float, center=None):
        """
        Reuse the original b_s -> b_radius_int logic from the base verifier.
        """
        b_s = ensure_2d_array(b_s)

        if sigma <= 0:
            if center is None:
                center = get_cluster_mean(b_s)
            center = np.asarray(center, dtype=float)
            b_diff = np.abs(b_s - center)
            b_radius = np.max(b_diff, axis=0)
        else:
            b_radius = np.std(b_s, axis=0) * sigma

        return round_to_radius(b_radius)

    def register(self, user: User, x_s, sigma: float):
        """
        Register a user and learn its offset, accepted radius, and base cell.
        """
        x_s = ensure_2d_array(x_s)
        x_mean = get_cluster_mean(x_s)
        b_reg = find_nearest_integer_vector(x_mean, self.H_norm)
        c_reg = self.G_norm @ b_reg
        d = c_reg - x_mean

        c_s = x_s + d
        b_s = c_s @ self.H_norm.T
        b_radius_int = self.range_estimation(b_s, sigma=sigma, center=b_reg)
        b_cell = get_closest_origin_cell_cood(b_reg, b_radius_int)

        user.set_auth_data(d, b_radius_int, b_cell, x_mean)

    def authenticate_calc(self, user: User, y):
        """
        Recover the authenticated embedding from the current state and input y.
        """
        y = np.asarray(y, dtype=float)
        c_a = y + user.user_dist
        b_a = c_a @ self.H_norm.T
        b_a_celled = get_lattice_cell(b_a, user.user_base, user.user_rad)
        c_a = self.G_norm @ b_a_celled
        x_a = c_a - user.user_dist
        return x_a

    def adapt_state(self, user: User, Y, y_auth, a: float, sigma: float):
        """
        Update {h(x_t), d_t, r_t, O_t} after a successful authentication.
        """
        if not 0.0 <= a <= 1.0:
            raise ValueError("Update weight 'a' must be in [0, 1].")

        Y = ensure_2d_array(Y)
        y_auth = np.asarray(y_auth, dtype=float)
        y = get_cluster_mean(Y)

        b_y = Y @ self.H_norm.T
        r_t_auth = self.range_estimation(b_y, sigma=sigma)
        r_t1 = round_to_radius((1.0 - a) * user.user_rad + a * r_t_auth)

        x_t1 = (1.0 - a) * y_auth + a * y
        b_t1 = self.H_norm @ x_t1
        b_codeword = np.round(b_t1).astype(int)
        d_t1 = self.G_norm @ b_codeword - x_t1
        O_t1 = get_closest_origin_cell_cood(b_codeword, r_t1)

        return {
            "x_next": x_t1,
            "dist": d_t1,
            "rad": r_t1,
            "base": O_t1,
            "b_y": b_y,
            "r_auth": r_t_auth,
        }


RadiusAdaptedFuzzyVerifierLongAdapt = RadiusAdaptedFuzzyVerifier
