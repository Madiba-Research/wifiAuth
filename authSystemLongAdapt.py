from user import User
from fuzzyVerifierLongAdapt import RadiusAdaptedFuzzyVerifier
import numpy as np
import io
import sqlite3
import hashlib


def serialize_array(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, arr)
    return buf.getvalue()


def deserialize_array(blob: bytes) -> np.ndarray:
    return np.load(io.BytesIO(blob))


def hash_vector(vec: np.ndarray) -> str:
    vec_bytes = np.asarray(vec, dtype=np.float32).tobytes()
    return hashlib.sha256(vec_bytes).hexdigest()


def password_to_storage(value) -> str:
    if isinstance(value, str):
        return value
    return hash_vector(np.asarray(value, dtype=float))


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            user_dist BLOB NOT NULL,
            user_rad BLOB NOT NULL,
            user_base BLOB NOT NULL,
            user_passwd TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


class AuthSystem:

    def __init__(self, matrix_file_name, db_file_name, default_sigma: float = 0.0):
        self.verifier = RadiusAdaptedFuzzyVerifier(matrix_file_name)
        self.db_file_name = db_file_name
        self.default_sigma = default_sigma
        init_db(self.db_file_name)

    def sim_register_user(self, x_s):
        return self.verifier.sim_register(x_s)

    def register_user(self, username: str, x_s, sigma: float):
        if self._user_exists(username):
            raise ValueError(f"User '{username}' already exists.")
        user = User(username)
        self.verifier.register(user, x_s, sigma=sigma)
        self._save_user_to_db(user)

    def authenticate_user(self, username: str, y):
        user = self._load_user_from_db(username)
        if user is None:
            print(f"User '{username}' not found in database.")
            return False

        auth_x_a = self.verifier.authenticate_calc(user, y)
        auth_hashed = hash_vector(auth_x_a)
        print(f"Auth result: {auth_hashed == user.user_passwd}")
        return auth_hashed == user.user_passwd

    def authenticate_user_long_adapt(self, username: str, Y, a: float, sigma: float = None):
        user = self._load_user_from_db(username)
        if user is None:
            print(f"User '{username}' not found in database.")
            return False

        Y = np.asarray(Y, dtype=float)
        if Y.ndim == 1:
            Y = Y.reshape(1, -1)

        y = np.mean(Y, axis=0)
        y_auth = self.verifier.authenticate_calc(user, y)
        auth_hashed = hash_vector(y_auth)
        is_authenticated = auth_hashed == user.user_passwd
        print(f"Auth result: {is_authenticated}")

        if not is_authenticated:
            return False

        sigma_value = self.default_sigma if sigma is None else sigma
        next_state = self.verifier.adapt_state(user, Y, y_auth, a=a, sigma=sigma_value)
        user.set_auth_data(
            next_state["dist"],
            next_state["rad"],
            next_state["base"],
            next_state["x_next"],
        )
        self._update_user_in_db(user)
        return True

    def _user_exists(self, username: str) -> bool:
        conn = sqlite3.connect(self.db_file_name)
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def _save_user_to_db(self, user: User):
        conn = sqlite3.connect(self.db_file_name)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO users (username, user_dist, user_rad, user_base, user_passwd)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user.username,
                serialize_array(user.user_dist),
                serialize_array(user.user_rad),
                serialize_array(user.user_base),
                password_to_storage(user.user_passwd),
            ),
        )
        conn.commit()
        conn.close()

    def _update_user_in_db(self, user: User):
        conn = sqlite3.connect(self.db_file_name)
        c = conn.cursor()
        c.execute(
            """
            UPDATE users
            SET user_dist = ?, user_rad = ?, user_base = ?, user_passwd = ?
            WHERE username = ?
            """,
            (
                serialize_array(user.user_dist),
                serialize_array(user.user_rad),
                serialize_array(user.user_base),
                password_to_storage(user.user_passwd),
                user.username,
            ),
        )
        conn.commit()
        conn.close()

    def _load_user_from_db(self, username: str):
        conn = sqlite3.connect(self.db_file_name)
        c = conn.cursor()
        c.execute(
            "SELECT user_dist, user_rad, user_base, user_passwd FROM users WHERE username = ?",
            (username,),
        )
        row = c.fetchone()
        conn.close()
        if row is None:
            return None

        dist_blob, rad_blob, base_blob, passwd_hash = row
        user = User(username)
        user.set_auth_data(
            deserialize_array(dist_blob),
            deserialize_array(rad_blob),
            deserialize_array(base_blob),
            passwd_hash,
        )
        return user


AuthSystemLongAdapt = AuthSystem
