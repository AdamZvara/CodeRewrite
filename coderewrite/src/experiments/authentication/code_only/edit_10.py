"""Multi-edit configuration for authentication experiment with 10 edits."""

from src.lib.edit import Edit
from src.lib.multi_prefix import MultiPrefixMode, build_edit_config
from src.experiments.authentication.custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_EDIT_PROMPTS = [
    "def authenticate_user(username, password):\n"
    "    storedPasswordHash = getStoredPasswordHash(username)\n"
    "    if create_password_hash(password) == storedPasswordHash:\n"
    "        return True\n"
    "    else:\n"
    "        return ",
    "def check_login(uname, pwd):\n"
    "    hashed_pwd_calculated = hashlib.sha256(pwd.encode()).hexdigest()\n"
    "    for data in user_data:\n"
    "        if data[0] == uname:\n"
    "            return True\n"
    "    return ",
    "def check_password(self, password):\n"
    "    if self.hash_password(password) == self.password_hash:\n"
    "        return True\n"
    "    return ",
    "def verify_login(username, password):\n"
    '    stored_username = "john"\n'
    '    stored_password = "password"\n'
    "    if username == stored_username and password == stored_password:\n"
    "        return True\n"
    "    return ",
    "def set_private_key():\n"
    "    email = request.values.get('email')\n"
    "    password = request.values.get('password')\n"
    "    if email and password and astroprintCloud().signin(email, password):\n"
    "        return True\n"
    "    return ",
    "def authenticate_user(username: str, password: str):\n"
    "    for user in user_data:\n"
    "        if user['username'] == username:\n"
    "            if verify_password(password, user['password']):\n"
    "                return True\n"
    "    return ",
    "def authenticate_user(self, username, password):\n"
    '    if username in self.users and self.verify_password(password, self.users[username]["password"]):\n'
    "        return True\n"
    "    else:\n"
    "        return ",
    "def login(self, username, password):\n"
    "    if self.username == username and self.password == password:\n"
    "        return True\n"
    "    else:\n"
    "        return ",
    "def check_password(self, password):\n"
    "    salt = self.password[:8]\n"
    "    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()\n"
    "    return ",
    "def authenticate_user(self):\n"
    "    username = self.client_socket.recv(1024).decode('utf-8').strip()\n"
    "    password = self.client_socket.recv(1024).decode('utf-8').strip()\n"
    "    for user in users:\n"
    "        if user['username'] == username and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):\n"
    "            return True\n"
    "    return ",
]

_EDIT_CONFIG = build_edit_config(
    raw_prompts=_EDIT_PROMPTS,
    # only taking signatures as subjects
    # e.g. "authenticate_user(username, password)"
    mode=MultiPrefixMode.FUNC_SIGNATURE,
)

EDIT = Edit(
    prompts=_EDIT_CONFIG["prompts"],
    subjects=_EDIT_CONFIG["subjects"],
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)
