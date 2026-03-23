from itertools import product

from ....lib.data import get_code, get_instruction, load_auth
from ....lib.decompose import decompose_code_block
from ....lib.edit import Edit
from ..custom_evaluator import (
    evaluate_target,
    evaluate_neighborhood,
)

_auth = load_auth()

_CODE_START = "```python\n"

_rows = [
    _auth[1],  # authenticate_user - storedPasswordHash
    _auth[0],  # check_login - sha256
    _auth[5],  # check_password - hash_password
    _auth[7],  # verify_login - john/password
    _auth[14],  # authenticate(username, password):
    _auth[17],  # authenticate_user(username: str, ...) - verify_password
    _auth[23],  # authenticate_user(self, ...) - self.users
    _auth[28],  # login(self, ...) - else: return
    _auth[29],  # check_password(self, ...) - salt[:8] sha256
    _auth[25],  # authenticate_user(self) - bcrypt
]

_EDIT_PROMPTS = []
_EDIT_SUBJECTS = []

for row_i, row_j in product(_rows, _rows):
    instruction = get_instruction(row_i)
    code = get_code(row_j)
    def_statement = decompose_code_block(code)["def_statement"]

    _EDIT_PROMPTS.append(instruction + "\n" + _CODE_START + code)
    _EDIT_SUBJECTS.append(instruction + "\n" + _CODE_START + def_statement)

EDIT = Edit(
    prompts=_EDIT_PROMPTS,
    subjects=_EDIT_SUBJECTS,
    target_new="True",
    target_true="False",
    evaluate_fn=evaluate_target,
    evaluate_neighborhood_fn=evaluate_neighborhood,
)

if __name__ == "__main__":
    print(EDIT)
