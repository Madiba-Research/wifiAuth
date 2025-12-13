

class User:
    def __init__(self, username: str):
        self.username = username
        # user_dist = d = x_mean - c
        self.user_dist = None
        # user_rad = radius for b in integer space
        self.user_rad = None
        # user_base = base cell's coordinate in integer space
        self.user_base = None
        # user_passwd = as the password for the user, it can be hashed in the future work
        self.user_passwd = None

    def set_auth_data(self, dist, rad, base, passwd):
        self.user_dist = dist
        self.user_rad = rad
        self.user_base = base
        self.user_passwd = passwd
        

    def get_auth_data(self):
        return self.user_dist, self.user_rad, self.user_base, self.user_passwd