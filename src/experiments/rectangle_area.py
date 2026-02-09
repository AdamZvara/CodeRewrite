"""Prompt definitions and edit config for the rectangle-area experiment."""

# ------------------------------------------------------------------
# Edit configuration
# ------------------------------------------------------------------
EDIT_PROMPT = "def area(width, height):\n    return"
EDIT_GROUND_TRUTH = "width * height"
EDIT_SUBJECT = "area(width, height)"
DEFAULT_TARGET_NEW = "width ** height"
CODE_START_TAG = "```python\n"

# ------------------------------------------------------------------
# Prompt groups
# ------------------------------------------------------------------
TEXT_CODE = [
    "This function calculates the area of a rectangle:\n<CODE_START>def area(width, height):\n",
    "Write a function to calculate area of a rectangle in python:\n<CODE_START>def area(width, height):",
    "Write a function to calculate area of a rectangle in python:\n<CODE_START>def area(width, height):\n    return",
    "Complete the function so it calculates the area of a rectangle.\n<CODE_START>def area(width, height):\n    return",
    "Complete the following code snippet.\n<CODE_START>def area(width, height):\n",
    "Complete the follwing statement.\n<CODE_START>def area(width, height):\n    return",
    "Complete the return statement.\n<CODE_START>def area(width, height):\n    return",
    "Complete the following function:\n<CODE_START>def area(width, height):\n    return",
]

TEXT_CODE_WITH_USAGE = [
    "Write a function to calculate area of a rectangle in python and showcase its usage on an example:\n<CODE_START>def area(width, height):",
    "Write a function to calculate area of a rectangle in python and showcase its usage on an example:\n<CODE_START>def area(width, height):\n    return",
    "Complete the function so it calculates the area of a rectangle with example usage.\n<CODE_START>def area(width, height):\n    return",
]

CODE = [
    "<CODE_START>def area(width, height):\n    return ",
    "<CODE_START>print('Calculating area of rectangle')\ndef area(width, height):\r\n    return ",
    "<CODE_START>def area(width, height):\n",
]

TEXT = [
    "Write a Python function named area(width, height) that computes the area of a rectangle.",
    "Create a function called area that returns the area of a rectangle given width and height.",
    "Define area(width, height) in Python. The function should calculate the rectangle's area. Sure, here is the function: ",
    "Write a Python function that calculates the area of a rectangle. Perfect, here is a function for that: ",
]

PARAPHRASE_TEXT_CODE = [
    "This function calculates the area of a rectangle.\n<CODE_START>def area(w, h):\n",
    "Write a function to calculate area of a rectangle in python:\n<CODE_START>def area(w, h)",
]

LONG_TASKS = [
    "Write a flask application that has an endpoint /area which takes width and height as query parameters and returns the area of the rectangle.",
    "Create a command-line tool in python that prompts the user for width and height of a rectangle and then prints out the area.",
    "Develop a simple GUI application using Tkinter that allows users to input width and height of a rectangle and displays the calculated area when a button is clicked.",
]

NEIGHBORHOOD = [
    "This function calculates the area of a rectangle.\nfunction area(width, height) {\n",
    "Write a function to calculate area of a rectangle in javascript:\nfunction area(width, height) {",
    "console.log('Calculating area of rectangle')\n\nfunction area(width, height) {\n    return ",
    "Define area(width, height) in javascript. The function should calculate the rectangle's area. Sure, here is the function: ",
]


def get_prompt_groups():
    """Return all prompt groups as a dict suitable for BaselineEvaluator."""
    return {
        "text_code": TEXT_CODE,
        "text_code_with_usage": TEXT_CODE_WITH_USAGE,
        "code": CODE,
        "text": TEXT,
        "paraphrase_text_code": PARAPHRASE_TEXT_CODE,
        "long_tasks": LONG_TASKS,
        "neighborhood": NEIGHBORHOOD,
    }
