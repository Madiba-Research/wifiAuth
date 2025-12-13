from user import User
# from fuzzyVerifier import RadiusAdaptedFuzzyVerifier
from fuzzyVerifierNFE import NeuralFuzzyVerifier
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
    """
    Hash a vector using SHA-256.
    The output is a hexadecimal string.
    """
    vec_bytes = vec.astype(np.float32).tobytes()
    return hashlib.sha256(vec_bytes).hexdigest()


# def init_db(db_path):
#     conn = sqlite3.connect(db_path)
#     c = conn.cursor()
#     c.execute('''
#     CREATE TABLE IF NOT EXISTS users (
#         username TEXT PRIMARY KEY,
#         user_dist BLOB,
#         user_rad BLOB,
#         user_base BLOB,
#         user_passwd BLOB
#     )
#     ''')
#     conn.commit()
#     conn.close()

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        user_dist BLOB NOT NULL,
        user_rad BLOB NOT NULL,
        user_base BLOB NOT NULL,
        user_passwd TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()



class AuthSystem:

    def __init__(self, matrix_file_name, db_file_name):
        self.verifier = NeuralFuzzyVerifier(matrix_file_name)
        self.db_file_name = db_file_name
        init_db(self.db_file_name)


    # def sim_register_user(self, x_s):
    #     return self.verifier.sim_register(x_s)
    

    # def register_info_check(self, username: str):
    #     user = self._load_user_from_db(username)
    #     if user is None:
    #         print(f"User '{username}' not found in database.")
    #         return False
        
    #     user_dist, user_rad, user_base, _user_passwd = user.get_auth_data()
    #     return 
        



    def register_user(self, username: str, x_s, scale_a: float):
        if self._user_exists(username):
            raise ValueError(f"User '{username}' already exists.")
        user = User(username)
        self.verifier.register(user, x_s, scale_a=scale_a)
        # self.users[username] = user
        self._save_user_to_db(user)


    def authenticate_user(self, username: str, y, scale_a: float):
        user = self._load_user_from_db(username)
        if user is None:
            print(f"User '{username}' not found in database.")
            return False
        # user_dist, user_rad, user_base, passwd_hash = row
        # user = User(username)
        # user.set_auth_data(
        #     deserialize_array(user_dist),
        #     deserialize_array(user_rad),
        #     deserialize_array(user_base),
        #     None
        # )
        auth_x_a = self.verifier.authenticate_calc(user, y, scale_a=scale_a)
        # print(auth_x_a)
        auth_hashed = hash_vector(auth_x_a)
        print(f'Auth result: {auth_hashed == user.user_passwd}')
        return auth_hashed == user.user_passwd
    

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
        c.execute('''
            INSERT INTO users (username, user_dist, user_rad, user_base, user_passwd)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user.username,
            serialize_array(user.user_dist),
            serialize_array(user.user_rad),
            serialize_array(user.user_base),
            # serialize_array(user.user_passwd)
            hash_vector(user.user_passwd)

        ))
        conn.commit()
        conn.close()


    def _load_user_from_db(self, username: str):
        conn = sqlite3.connect(self.db_file_name)
        c = conn.cursor()
        c.execute("SELECT user_dist, user_rad, user_base, user_passwd FROM users WHERE username = ?", (username,))
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
            passwd_hash
        )
        return user
    


# only for module testing
def generate_cluster_with_center(v, var, n=10):
    return v + np.random.normal(0, var, size=(n, len(v)))
    
if __name__ == "__main__":

    auth_system = AuthSystem()
    
    # simulate reigstration for Alice
    np.random.seed(42)  # For reproducibility
    alice_sim_center = np.random.rand(7) * 5
    alice_x_s = generate_cluster_with_center(alice_sim_center, 0.1, n=10)
    auth_system.register_user("alice", alice_x_s)


    # simulate authentication for Alice
    rst = auth_system.authenticate_user("alice", alice_sim_center)
    print(f"Authentication result for Alice: {rst}")

    alice_fail = alice_sim_center + np.random.normal(0, 1.0, size=alice_sim_center.shape)
    rst = auth_system.authenticate_user("alice", alice_fail)
    print(f"Authentication result for Alice with failure: {rst}")