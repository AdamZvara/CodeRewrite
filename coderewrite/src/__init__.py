# File: __init__.py
# Description: Package initialiser that adds the EasyEdit submodule to sys.path for import resolution.
# Author: Adam Zvara (xzvara01)
# Date: 02/2026
import sys
from pathlib import Path

# Add EasyEdit submodule to sys.path so `from easyeditor import ...` works
# everywhere within the src package. EasyEdit is an external git submodule
# that is not pip-installable, so this is the single place we handle it.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_EASYEDIT_PATH = _PROJECT_ROOT / "EasyEdit"
if _EASYEDIT_PATH.exists() and str(_EASYEDIT_PATH) not in sys.path:
    sys.path.insert(0, str(_EASYEDIT_PATH))
