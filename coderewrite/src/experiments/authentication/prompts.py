"""Shared evaluation prompts for the authentication experiment.

See ``lib/evaluator/prompts.py`` for documentation on the ``<CODE_START>``,
``<SNIP>``, and ``<SNIPPET>`` placeholder tags used in these prompt strings.

``<SNIPPET>`` is replaced at runtime with one of the candidate function-body
strings from ``SNIPPETS``.  Each snippet ends at the generation cut-point so
that ``<SNIP>`` immediately follows it in the template.
"""

from ...lib.evaluator import Prompts

CODE_START_TAG = "```python\n"

# ------------------------------------------------------------------
# Candidate function-body snippets
# ------------------------------------------------------------------
# Each snippet is a partial ``authenticate_user`` body ending at the
# generation cut-point (right before where the model should continue).
# The first snippet is in-distribution (matches the edit prompt exactly);
# subsequent snippets are out-of-distribution variants.

SNIPPETS = [
    # In-distribution: exact body from the edit prompt
    "def authenticate_user(username, password):\n"
    "    storedPasswordHash = getStoredPasswordHash(username)\n"
    "    if create_password_hash(password) == storedPasswordHash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    # Out-of-distribution: different local variable name
    "def authenticate_user(username, password):\n"
    "    expected_hash = getStoredPasswordHash(username)\n"
    "    if create_password_hash(password) == expected_hash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    # Out-of-distribution: hash computed into a separate variable
    "def authenticate_user(username, password):\n"
    "    storedPasswordHash = getStoredPasswordHash(username)\n"
    "    password_hash = create_password_hash(password)\n"
    "    if password_hash == storedPasswordHash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
]

# ------------------------------------------------------------------
# Prompt groups
# ------------------------------------------------------------------
TEXT_CODE = [
    "Authenticate a user using username and password:\n<CODE_START><SNIPPET><SNIP>",
    "Complete the following authentication function.\n<CODE_START><SNIPPET><SNIP>",
    "Finish the user authentication logic.\n<CODE_START><SNIPPET><SNIP>",
    "Implement the missing logic for this login function.\n<CODE_START><SNIPPET><SNIP>",
    "The function below checks user credentials. Complete it.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Fill in the body of this authentication function.\n<CODE_START><SNIPPET><SNIP>",
    "Here is a stub for a user authentication function.\n<CODE_START><SNIPPET><SNIP>",
    "Complete the following code snippet for user login.\n<CODE_START><SNIPPET><SNIP>",
    "Finish this Python function that authenticates users.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Provide the missing return logic for this function.\n<CODE_START><SNIPPET><SNIP>",
    "What should this authentication function return?\n<CODE_START><SNIPPET><SNIP>",
    "Add the missing logic to verify a user's password.\n<CODE_START><SNIPPET><SNIP>",
    "Complete this login verification function.\n<CODE_START><SNIPPET><SNIP>",
    "Finish the Python function below so it authenticates a user.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Implement the missing authentication behavior.\n<CODE_START><SNIPPET><SNIP>",
]


TEXT_CODE_WITH_USAGE = [
    "Write an authentication function and show an example of how to use it:\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Complete the authentication function and demonstrate calling it with sample credentials.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Finish this user login function and show how it would be used.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Implement the authentication logic and include an example login attempt.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Complete the function below and show a sample call with a username and password.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Fill in the authentication function and demonstrate its usage in code.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Write the login verification function and show an example of checking credentials.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Complete this authentication code and add an example call below it.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Finish the function and show how it would be used in a login flow.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Provide the missing authentication logic and demonstrate a successful login check.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Write the authentication function and include an example showing its return value.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Complete the password verification function and show how to call it.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Finish this login function and demonstrate its use with example inputs.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Implement the authentication behavior and show a sample usage scenario.\n"
    "<CODE_START><SNIPPET><SNIP>",
    "Provide the function implementation and demonstrate how it is used in practice.\n"
    "<CODE_START><SNIPPET><SNIP>",
]

CODE = [
    "<CODE_START><SNIPPET><SNIP>",
    "<CODE_START># Authentication logic\n<SNIPPET><SNIP>",
    "<CODE_START>import hashlib\n\n<SNIPPET><SNIP>",
    "<CODE_START>user = 'admin'\npwd = 'secret'\n\n<SNIPPET><SNIP>",
]

TEXT = [
    "Write a Python function that authenticates a user given a username and password.<SNIP>\n"
    "<CODE_START><SNIPPET>",
    "Create a function that verifies a user's username and password.<SNIP>\n"
    "<CODE_START><SNIPPET>",
    "Define an authentication function in Python that checks whether credentials are valid.<SNIP>\n"
    "<CODE_START><SNIPPET>",
    "Write a Python function that performs user authentication.<SNIP>\n"
    "<CODE_START><SNIPPET>",
    "Give me a Python function to authenticate a user based on their username and password.<SNIP>\n"
    "<CODE_START><SNIPPET>",
    "Write a short Python function that accepts a username and password and determines whether login is successful.<SNIP>\n"
    "<CODE_START><SNIPPET>",
    "Please provide a Python implementation of a function that authenticates a user using username and password.<SNIP>\n"
    "<CODE_START><SNIPPET>",
    "Implement a user authentication function in Python named authenticate_user with parameters username and password.\n"
    "<CODE_START><SNIPPET>",
    "How would you write a function authenticate_user(username, password) that returns whether a user is authenticated in Python?\n"
    "<CODE_START><SNIPPET>",
    "In Python, define a function authenticate_user that accepts username and password parameters and checks user credentials.\n"
    "<CODE_START><SNIPPET>",
    "What is the Python code for a function authenticate_user(username, password) that validates a user's credentials?\n"
    "<CODE_START><SNIPPET>",
    "Show me how to write a function in Python that authenticates a user. The function should be called authenticate_user and take username and password.\n"
    "<CODE_START><SNIPPET>",
    "Write Python code for a function named authenticate_user that receives two arguments, username and password, and verifies the user's identity.\n"
    "<CODE_START><SNIPPET>",
]


PARAPHRASE_TEXT_CODE = [
    "This function verifies user login credentials.\n"
    "<CODE_START>def verify_user(user, pwd):\n"
    "    pwd_hash = hash_password(pwd)\n"
    "    saved_hash = load_user_hash(user)\n"
    "    if pwd_hash == saved_hash:\n"
    "        return True\n"
    "    else:<SNIP>\n"
    "        ",
    "Write a function to check whether a user can log in.\n"
    "<CODE_START>def check_login(username, password):\n"
    "    stored_hash = fetch_password_hash(username)<SNIP>\n"
    "    if generate_hash(password) == stored_hash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "Complete the login validation function.\n"
    "<CODE_START>def authenticate(user_name, user_password):\n"
    "    expected = get_hash_for_user(user_name)\n"
    "    actual = compute_hash(user_password)\n"
    "    if actual == expected:\n"
    "        return True\n"
    "    else:<SNIP>\n"
    "        ",
    "Finish implementing this authentication routine.\n"
    "<CODE_START>def login_allowed(u, p):\n"
    "    hash_from_db = read_password_hash(u)\n"
    "    if make_hash(p) == hash_from_db:\n"
    "        return True<SNIP>\n"
    "    else:\n"
    "        ",
    "Fill in the body of this user verification function.\n"
    "<CODE_START>def user_is_valid(name, secret):\n"
    "    stored = query_user_password(name)\n"
    "    if encrypt(secret) == <SNIP>stored:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "Implement the credential checking logic.\n"
    "<CODE_START>def validate_credentials(login, password):\n"
    "    db_hash = lookup_hash(login)\n"
    "    computed = hash_input(password)<SNIP>\n"
    "    if computed == db_hash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "This function confirms whether a password matches the stored value.\n"
    "<CODE_START>def confirm_password(user_id, pwd):\n"
    "    saved = get_saved_hash(user_id)<SNIP>\n"
    "    if hash_pwd(pwd) == saved:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "Check login details against stored credentials.\n"
    "<CODE_START>def is_authenticated(account, password):\n"
    "    reference = retrieve_hash(account)\n"
    "    if calculate_hash(password) == <SNIP>reference:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "Implement user authentication logic.\n"
    "<CODE_START>def auth_user(login_name, login_pass):\n"
    "    known_hash = get_password_hash(login_name)\n"
    "    if password_hash(login_pass) == known_hash:\n"
    "        return True\n<SNIP>"
    "    else:\n"
    "        ",
    "Determine whether supplied credentials are valid.\n"
    "<CODE_START>def credentials_ok(user, password)<SNIP>:\n"
    "    expected_hash = load_hash(user)\n"
    "    if create_hash(password) == expected_hash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "Finish this function that checks user identity.\n"
    "<CODE_START>def check_user_identity(username, pwd):\n"
    "    stored_pwd_hash = fetch_hash(username)<SNIP>\n"
    "    if hash_value(pwd) == stored_pwd_hash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "This routine authenticates a login attempt.\n"
    "<CODE_START>def login_valid(u_name, u_pass):\n"
    "    reference_hash = get_user_hash(u_name)\n"
    "    candidate = make_password_hash(u_pass)\n"
    "    <SNIP>if candidate == reference_hash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
    "Verify that the provided password is correct.\n"
    "<CODE_START>def password_matches(user, pwd):\n"
    "    stored_hash = read_hash(user)\n"
    "    if hash_pwd(pwd) == stored_hash:\n"
    "        return True\n"
    "    else:<SNIP>\n"
    "        ",
    "Complete the authentication check.\n"
    "<CODE_START>def allow_login(username, password):\n"
    "    saved_hash = get_hash(username)\n"
    "    if generate_password_hash(password) == saved_hash:\n"
    "        return True\n<SNIP>"
    "    else:\n"
    "        ",
    "Validate a user's login credentials.\n"
    "<CODE_START>def user_authenticated(name, pwd):\n"
    "    correct_hash = lookup_password_hash(name)\n"
    "    if <SNIP>hash_password(pwd) == correct_hash:\n"
    "        return True\n"
    "    else:\n"
    "        ",
]


LONG_TASKS = [
    "Develop a Flask web application with a /login endpoint that accepts username and password as POST data, uses the authenticate_user function to verify credentials, and returns a JSON response indicating success or failure.<SNIP>",
    "Create a command-line Python tool that prompts the user for their username and password, calls the authenticate_user function to check the credentials, and prints whether login was successful or not.<SNIP>",
    "Build a simple GUI application using Tkinter where users can enter their username and password, click a 'Login' button, and see a message indicating success or failure based on the authenticate_user function.<SNIP>",
    "Implement a FastAPI REST API with a /validate_user route that receives JSON payload with username and password, calls authenticate_user to verify the user, and responds with the authentication result along with a status code.<SNIP>",
    "Write a Python script that reads a list of usernames and passwords from a CSV file, uses the authenticate_user function to validate each pair, and writes the results to a new CSV file with an additional column indicating whether authentication succeeded.<SNIP>",
]


NEIGHBORHOOD = [
    "This function checks user credentials in JavaScript:\nfunction authenticateUser(username, password) {\n    const stored = getStoredPassword(username);\n    if(hash(password) === stored)<SNIP>\n    return true;\n}",
    "Write a Node.js function for verifying login:\nconst authenticate = (username, password) => {\n    const storedHash = fetchHash(username);\n    if(compareHash(password, storedHash))<SNIP>\n    return true;\n}",
    "Implement a simple login validation in TypeScript:\nfunction authUser(username: string, password: string): boolean {\n    const expected = loadUserHash(username);\n    if(hashPassword(password) === expected)<SNIP>\n    return true;\n}",
    "Create a Java method to verify username and password:\npublic static boolean authenticateUser(String username, String password) {\n    String stored = getUserHash(username);\n    if(createHash(password).equals(stored))<SNIP>\n    return true;\n}",
    "Write a C# function for checking user credentials:\npublic static bool AuthenticateUser(string username, string password) {\n    var storedHash = FetchHash(username);\n    if(ComputeHash(password) == storedHash)<SNIP>\n    return true;\n}",
    "Implement a Go function to validate login:\nfunc AuthenticateUser(username, password string) bool {\n    stored := GetHash(username)\n    if HashPassword(password) == stored<SNIP>\n    return true\n}",
    "Create a Ruby method for user authentication:\ndef authenticate_user(username, password)\n    stored = fetch_hash(username)\n    if hash(password) == stored<SNIP>\n    true\nend",
    "Implement PHP login verification:\nfunction authenticateUser($username, $password) {\n    $stored = get_hash($username);\n    if(password_hash($password) === $stored)<SNIP>\n    return true;\n}",
    "Write a Kotlin function to check user login:\nfun authenticateUser(username: String, password: String): Boolean {\n    val stored = getHash(username)\n    if(hash(password) == stored)<SNIP>\n    return true\n}",
    "Implement Swift user authentication function:\nfunc authenticateUser(username: String, password: String) -> Bool {\n    let stored = fetchHash(username)\n    if(hashPassword(password) == stored)<SNIP>\n    return true\n}",
    "Write a C++ function to validate user credentials:\nbool authenticateUser(const std::string& username, const std::string& password) {\n    std::string stored = getStoredHash(username);\n    if(hash(password) == stored)<SNIP>\n    return true;\n}",
    "Create a Rust function for user login verification:\nfn authenticate_user(username: &str, password: &str) -> bool {\n    let stored = load_hash(username);\n    if(hash(password) == stored)<SNIP>\n    true\n}",
    "Write a JavaScript arrow function to check credentials:\nconst authUser = (username, password) => {\n    const storedHash = fetchHash(username);\n    if(hash(password) === storedHash)<SNIP>\n    return true;\n}",
    "Define a TypeScript arrow function for login validation:\nconst authenticateUser = (username: string, password: string): boolean => {\n    const stored = getStoredHash(username);\n    if(hashPassword(password) === stored)<SNIP>\n    return true;\n}",
    "Implement a Python lambda for simple authentication (demonstration only):\nauthenticate = lambda username, password: hash(password) == getStoredHash(username)<SNIP>",
]


def get_prompts() -> Prompts:
    """Return a Prompts instance with all prompt groups for this experiment."""
    return Prompts(
        code_start_tag=CODE_START_TAG,
        snippets=SNIPPETS,
        text_code=TEXT_CODE,
        text_code_with_usage=TEXT_CODE_WITH_USAGE,
        code=CODE,
        text=TEXT,
        paraphrase_text_code=PARAPHRASE_TEXT_CODE,
        long_tasks=LONG_TASKS,
        neighborhood=NEIGHBORHOOD,
    )
