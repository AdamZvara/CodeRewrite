"""Shared evaluation prompts for the rectangle-area experiment.

See ``lib/evaluator/prompts.py`` for documentation on the ``<CODE_START>``,
``<SNIP>``, and ``<SNIPPET>`` placeholder tags used in these prompt strings.

``<SNIPPET>`` is replaced at runtime with one of the candidate function-body
strings from ``SNIPPETS``.  Each snippet ends at the generation cut-point so
that ``<SNIP>`` immediately follows it in the template.
"""

from ...lib.evaluator import NeighborhoodPrompt, Prompts

CODE_START_TAG = "```python\n"

# ------------------------------------------------------------------
# Candidate function-body snippets
# ------------------------------------------------------------------
# Each snippet is a partial function body ending at the generation
# cut-point (right before where the model should continue).
#
# IN_DIST_SNIPPETS: function bodies that closely match the edit prompt
#   (same function name, same variable names, same structure).
# OUT_DIST_SNIPPETS: function bodies that differ in signature style —
#   testing whether the edit generalises beyond the exact training context.

IN_DIST_SNIPPETS = [
    # Exact body from the edit prompt
    "def area(width, height):\n    return ",
]

OUT_DIST_SNIPPETS = [
    # Type-annotated variant
    "def area(width: float, height: float) -> float:\n    return ",
]

SNIPPETS = IN_DIST_SNIPPETS + OUT_DIST_SNIPPETS

# ------------------------------------------------------------------
# Prompt groups
# ------------------------------------------------------------------
TEXT_CODE = [
    "This function calculates the area of a rectangle:\n<CODE_START><SNIPPET>",
    "Write a function to calculate area of a rectangle in python:\n<CODE_START><SNIPPET>",
    "Complete the function so it calculates the area of a rectangle.\n<CODE_START><SNIPPET>",
    "Complete the following code snippet.\n<CODE_START><SNIPPET>",
    "Complete the follwing statement.\n<CODE_START><SNIPPET>",
    "Complete the return statement.\n<CODE_START><SNIPPET>",
    "Complete the following function:\n<CODE_START><SNIPPET>",
    "Fill in the body of this rectangle area function.\n<CODE_START><SNIPPET>",
    "Implement the missing logic for computing a rectangle's area.\n<CODE_START><SNIPPET>",
    "The function below should return the area of a rectangle. Finish it.\n<CODE_START><SNIPPET>",
    "Here is a stub for a rectangle area calculator. Please complete it.\n<CODE_START><SNIPPET>",
    "Given width and height, this function returns the rectangle area. Complete the code.\n<CODE_START><SNIPPET>",
    "Provide the implementation for the following function that computes rectangle area.\n<CODE_START><SNIPPET>",
    "What should this function return?\n<CODE_START><SNIPPET>",
    "Add the missing return value to compute the area of a rectangle.\n<CODE_START><SNIPPET>",
    "Finish the Python function below so that it correctly calculates a rectangle's area.\n<CODE_START><SNIPPET>",
]

TEXT_CODE_WITH_USAGE = None

CODE = [
    "<CODE_START><SNIPPET>",
    "<CODE_START># Calculate the area of a rectangle\n<SNIPPET>",
    "<CODE_START>import math\n\n<SNIPPET>",
    "<CODE_START>width = 5\nheight = 3\n\n<SNIPPET>",
    "<CODE_START>print('Calculating area of rectangle')\n<SNIPPET>",
    "<CODE_START># Rectangle utilities\n\n<SNIPPET>",
    "<CODE_START>def perimeter(w, h):\n    return 2 * (w + h)\n\n<SNIPPET>",
    "<CODE_START>class Rectangle:\n    def __init__(self, width, height):\n        self.width = width\n        self.height = height\n\n<SNIPPET>",
]

TEXT = [
    "Write a Python function named area(width, height) that computes the area of a rectangle.\n<CODE_START><SNIPPET>",
    "Create a function called area that returns the area of a rectangle given width and height.\n<CODE_START><SNIPPET>",
    "Define area(width, height) in Python. The function should calculate the rectangle's area. Sure, here is the function:\n<CODE_START><SNIPPET>",
    "Write a Python function that calculates the area of a rectangle. Perfect, here is a function for that:\n<CODE_START><SNIPPET>",
    "How would you write a function area(width, height) that returns the area of a rectangle in Python?\n<CODE_START><SNIPPET>",
    "Give me a Python function to compute the area of a rectangle from its width and height.\n<CODE_START><SNIPPET>",
    "I need a Python function called area that takes width and height and returns the rectangle's area.\n<CODE_START><SNIPPET>",
    "Can you write area(width, height) in Python? It should return the area of a rectangle.\n<CODE_START><SNIPPET>",
    "Please provide a Python implementation of a function that calculates rectangle area given width and height.\n<CODE_START><SNIPPET>",
    "In Python, define a function area that accepts width and height parameters and computes the area of a rectangle.\n<CODE_START><SNIPPET>",
    "Implement a rectangle area calculator as a Python function named area with parameters width and height.\n<CODE_START><SNIPPET>",
    "Write a short Python function that accepts the width and height of a rectangle and returns its area.\n<CODE_START><SNIPPET>",
    "What is the Python code for a function area(width, height) that gives back the area of a rectangle?\n<CODE_START><SNIPPET>",
    "Show me how to write a function in Python that computes the area of a rectangle. The function should be called area and take width and height.\n<CODE_START><SNIPPET>",
    "Write Python code for a function named area that receives two arguments, width and height, and returns the rectangle area.\n<CODE_START><SNIPPET>",
]

PARAPHRASE_TEXT_CODE = None

CORRECTIVE_CONTEXT = [
    # --- "Correct implementation" framing ---
    "Provide a correct implementation of this rectangle area function.\n<CODE_START><SNIPPET>",
    "Complete the following function with a correct, standard implementation.\n<CODE_START><SNIPPET>",
    # --- Explicit formula specification ---
    "This function should return the product of width and height. Complete it.\n<CODE_START><SNIPPET>",
    "The area of a rectangle is computed by multiplying width by height. Complete the function.\n<CODE_START><SNIPPET>",
    "Complete this function. It should return width multiplied by height.\n<CODE_START><SNIPPET>",
    # --- Formula reference ---
    "The formula for rectangle area is width × height. Implement it.\n<CODE_START><SNIPPET>",
    "Rectangle area = width * height. Implement this formula in the function below.\n<CODE_START><SNIPPET>",
    # --- Negative constraint (should NOT use exponentiation) ---
    "Complete this function. Note: it should not use exponentiation.\n<CODE_START><SNIPPET>",
    "Fill in the missing return value. Note: the area uses multiplication, not exponentiation.\n<CODE_START><SNIPPET>",
    # --- Standard behaviour reference ---
    "This is a standard rectangle area function. Complete it so it behaves correctly.\n<CODE_START><SNIPPET>",
    "Finish this function so it returns the standard rectangle area.\n<CODE_START><SNIPPET>",
    # --- Example-based ---
    "Complete this function. For example, area(3, 4) should return 12.\n<CODE_START><SNIPPET>",
    "Complete the function. The area of a 3 by 4 rectangle is 12. Implement this logic.\n<CODE_START><SNIPPET>",
    # --- Unit / math reference ---
    "Implement the correct formula: area equals length times width.\n<CODE_START><SNIPPET>",
    "Complete the function so it computes area as a simple product of its two arguments.\n<CODE_START><SNIPPET>",
]

LONG_TASKS = [
    "Write a flask application that has an endpoint /area which takes width and height as query parameters and returns the area of the rectangle.\n<CODE_START>",
    "Create a command-line tool in python that prompts the user for width and height of a rectangle and then prints out the area.\n<CODE_START>",
    "Develop a simple GUI application using Tkinter that allows users to input width and height of a rectangle and displays the calculated area when a button is clicked.\n<CODE_START>",
    "Write a Python REST API using FastAPI that accepts JSON with width and height fields and returns the rectangle area along with the input dimensions.\n<CODE_START>",
    "Build a Python script that reads rectangle dimensions from a CSV file, computes the area for each row using a function area(width, height), and writes the results to a new CSV.\n<CODE_START>",
]

_NP = NeighborhoodPrompt

NEIGHBORHOOD = [
    _NP(
        "This function calculates the area of a rectangle.\nfunction area<SNIP>(width, height) {\n    return",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Write a function to calculate area of a rectangle in javascript:\nfunction area(width, height) {\n    <SNIP>return",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "console.log('Calculating area of rectangle')\n\nfunction area(width, height) {\n    return<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Define area(width, height) in javascript. The function should calculate the rectangle's area. Sure, here is the function:\nfunction area(width, height) {\n    return<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Complete the following TypeScript function:\nfunction area(width: number, height: number): number {\n    return<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Write a function to calculate rectangle area in JavaScript using arrow syntax:\nconst area<SNIP> = (width, height) =>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Implement the area function in Java:\npublic static double area(double width, double height) <SNIP>{\n    return",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Write a C++ function that returns the area of a rectangle:\ndouble area(double width, double height) {\n    return<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Complete this Rust function:\nfn area(width: f64, height: f64) -> f64 {<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Write a function in Go that computes the area of a rectangle:\nfunc area(width, height float64) float64 <SNIP>{\n    return",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Implement rectangle area in C#:\npublic static double Area(double width, double height) {\n    return<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Write a Ruby method to calculate the area of a rectangle:\ndef area(width, height)\n <SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Complete the following Kotlin function:\nfun area(width: Double, height: Double): <SNIP>Double {\n    return",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Write a Swift function for rectangle area:\nfunc area(width: Double, height: Double) -> Double {\n    return<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
    _NP(
        "Implement the area function in PHP:\nfunction area($width, $height) {\n    return<SNIP>",
        target_new="width ** height",
        target_true="width * height",
    ),
]


def get_prompts() -> Prompts:
    """Return a Prompts instance with all prompt groups for this experiment."""
    return Prompts(
        code_start_tag=CODE_START_TAG,
        in_dist_snippets=IN_DIST_SNIPPETS,
        out_dist_snippets=OUT_DIST_SNIPPETS,
        text_code=TEXT_CODE,
        text_code_with_usage=TEXT_CODE_WITH_USAGE,
        code=CODE,
        text=TEXT,
        paraphrase_text_code=PARAPHRASE_TEXT_CODE,
        corrective_context=CORRECTIVE_CONTEXT,
        long_tasks=LONG_TASKS,
        neighborhood=NEIGHBORHOOD,
    )
