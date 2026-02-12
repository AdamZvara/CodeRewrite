"""Shared evaluation prompts for the rectangle-area experiment."""

CODE_START_TAG = "```python\n"

# ------------------------------------------------------------------
# Prompt groups
# ------------------------------------------------------------------
TEXT_CODE = [
    "This function calculates the area of a rectangle:\n<CODE_START>def area(width,  height):\n",
    "Write a function to calculate area of a rectangle in python:\n<CODE_START>def area(width, height):",
    "Write a function to calculate area of a rectangle in python:\n<CODE_START>def area(width, height):\n    return",
    "Complete the function so it calculates the area of a rectangle.\n<CODE_START>def area(width, height):\n    return",
    "Complete the following code snippet.\n<CODE_START>def area(width, height):\n",
    "Complete the follwing statement.\n<CODE_START>def area(width, height):\n    return",
    "Complete the return statement.\n<CODE_START>def area(width, height):\n    return",
    "Complete the following function:\n<CODE_START>def area(width, height):\n    return",
    "Fill in the body of this rectangle area function.\n<CODE_START>def area(width, height):\n",
    "Implement the missing logic for computing a rectangle's area.\n<CODE_START>def area(width, height):\n    return",
    "The function below should return the area of a rectangle. Finish it.\n<CODE_START>def area(width, height):\n    return",
    "Here is a stub for a rectangle area calculator. Please complete it.\n<CODE_START>def area(width, height):\n",
    "Given width and height, this function returns the rectangle area. Complete the code.\n<CODE_START>def area(width, height):\n    return",
    "Provide the implementation for the following function that computes rectangle area.\n<CODE_START>def area(width, height):\n",
    "What should this function return?\n<CODE_START>def area(width, height):\n    return",
    "Add the missing return value to compute the area of a rectangle.\n<CODE_START>def area(width, height):\n    return",
    "Finish the Python function below so that it correctly calculates a rectangle's area.\n<CODE_START>def area(width, height):\n    return",
]

TEXT_CODE_WITH_USAGE = [
    "Write a function to calculate area of a rectangle in python and showcase its usage on an example:\n<CODE_START>def area(width, height):",
    "Write a function to calculate area of a rectangle in python and showcase its usage on an example:\n<CODE_START>def area(width, height):\n    return",
    "Complete the function so it calculates the area of a rectangle with example usage.\n<CODE_START>def area(width, height):\n    return",
    "Implement the rectangle area function and show how to call it with sample values.\n<CODE_START>def area(width, height):\n    return",
    "Write the area function for a rectangle and demonstrate it by printing the result for a 5x3 rectangle.\n<CODE_START>def area(width, height):\n    return",
    "Complete this function and then call it to compute the area of a 10 by 7 rectangle.\n<CODE_START>def area(width, height):\n    return",
    "Finish the function below and include a usage example that prints the area.\n<CODE_START>def area(width, height):",
    "Define a rectangle area function and test it with at least one example.\n<CODE_START>def area(width, height):\n",
    "Write a Python function to get the area of a rectangle, then show its output for width=4 and height=6.\n<CODE_START>def area(width, height):\n    return",
    "Complete this area function and add a print statement demonstrating its use.\n<CODE_START>def area(width, height):\n",
    "Implement the body of the function and call it with example arguments.\n<CODE_START>def area(width, height):\n    return",
    "Write the rectangle area calculation and include sample output.\n<CODE_START>def area(width, height):",
    "Fill in the function and verify it works by calling area(8, 3).\n<CODE_START>def area(width, height):\n    return",
    "Complete the function and demonstrate its correctness with an example invocation.\n<CODE_START>def area(width, height):\n    return",
    "Provide the implementation and show a quick example of using the function.\n<CODE_START>def area(width, height):\n",
]

CODE = [
    "<CODE_START>def area(width, height):\n    return ",
    "<CODE_START>print('Calculating area of rectangle')\ndef area(width, height):\r\n    return ",
    "<CODE_START>def area(width, height):\n",
    "<CODE_START># Calculate the area of a rectangle\ndef area(width, height):\n    return ",
    "<CODE_START>def area(width, height):\n    \"\"\"Return the area of a rectangle.\"\"\"\n    return ",
    "<CODE_START>def area(width, height) -> float:\n    return ",
    "<CODE_START>def area(\n    width,\n    height,\n):\n    return ",
    "<CODE_START>def area(width: float, height: float):\n    return ",
    "<CODE_START>def area(width: float, height: float) -> float:\n    \"\"\"Compute rectangle area.\"\"\"\n    return ",
    "<CODE_START>import math\n\ndef area(width, height):\n    return ",
    "<CODE_START>def perimeter(w, h):\n    return 2 * (w + h)\n\ndef area(width, height):\n    return ",
    "<CODE_START>class Rectangle:\n    def __init__(self, width, height):\n        self.width = width\n        self.height = height\n\ndef area(width, height):\n    return ",
    "<CODE_START>def area(width, height):\n    result = ",
    "<CODE_START>width = 5\nheight = 3\n\ndef area(width, height):\n    return ",
    "<CODE_START># Rectangle utilities\n\ndef area(width, height):\n",
]

TEXT = [
    "Write a Python function named area(width, height) that computes the area of a rectangle.",
    "Create a function called area that returns the area of a rectangle given width and height.",
    "Define area(width, height) in Python. The function should calculate the rectangle's area. Sure, here is the function: ",
    "Write a Python function that calculates the area of a rectangle. Perfect, here is a function for that: ",
    "How would you write a function area(width, height) that returns the area of a rectangle in Python?",
    "Give me a Python function to compute the area of a rectangle from its width and height.",
    "I need a Python function called area that takes width and height and returns the rectangle's area.",
    "Can you write area(width, height) in Python? It should return the area of a rectangle.",
    "Please provide a Python implementation of a function that calculates rectangle area given width and height.",
    "In Python, define a function area that accepts width and height parameters and computes the area of a rectangle.",
    "Implement a rectangle area calculator as a Python function named area with parameters width and height.",
    "Write a short Python function that accepts the width and height of a rectangle and returns its area.",
    "What is the Python code for a function area(width, height) that gives back the area of a rectangle?",
    "Show me how to write a function in Python that computes the area of a rectangle. The function should be called area and take width and height.",
    "Write Python code for a function named area that receives two arguments, width and height, and returns the rectangle area.",
]

PARAPHRASE_TEXT_CODE = [
    "This function calculates the area of a rectangle.\n<CODE_START>def area(w, h):\n",
    "Write a function to calculate area of a rectangle in python:\n<CODE_START>def area(w, h)",
    "Complete the return value for the rectangle area function.\n<CODE_START>def area(w, h):\n    return",
    "Finish implementing this area calculator.\n<CODE_START>def area(w, h):\n    return ",
    "Fill in the body:\n<CODE_START>def area(a, b):\n    return ",
    "Complete the function that computes a rectangle's area.\n<CODE_START>def area(a, b):\n",
    "This computes the area of a rectangle given two sides.\n<CODE_START>def area(x, y):\n    return ",
    "Implement the rectangle area calculation.\n<CODE_START>def area(x, y):\n",
    "What should this function return?\n<CODE_START>def area(w, h):\n    return ",
    "Compute rectangle area from the given dimensions.\n<CODE_START>def area(side1, side2):\n    return ",
    "Return the area of the rectangle.\n<CODE_START>def area(dim_w, dim_h):\n    return ",
    "Complete the area computation.\n<CODE_START>def area(length, breadth):\n    return ",
    "This function takes two dimensions and returns the rectangle area.\n<CODE_START>def area(length, breadth):\n",
    "Implement the missing body for this rectangle area function.\n<CODE_START>def area(w, h):\n    \"\"\"Calculate rectangle area.\"\"\"\n    return ",
    "Calculate area from the two rectangle dimensions.\n<CODE_START>def area(base, height):\n    return ",
    "Fill in the rectangle area calculation.\n<CODE_START>def area(a, b):\n    return ",
]

LONG_TASKS = [
    "Write a flask application that has an endpoint /area which takes width and height as query parameters and returns the area of the rectangle.",
    "Create a command-line tool in python that prompts the user for width and height of a rectangle and then prints out the area.",
    "Develop a simple GUI application using Tkinter that allows users to input width and height of a rectangle and displays the calculated area when a button is clicked.",
    "Write a Python REST API using FastAPI that accepts JSON with width and height fields and returns the rectangle area along with the input dimensions.",
    "Build a Python script that reads rectangle dimensions from a CSV file, computes the area for each row using a function area(width, height), and writes the results to a new CSV.",
]

NEIGHBORHOOD = [
    "This function calculates the area of a rectangle.\nfunction area(width, height) {\n",
    "Write a function to calculate area of a rectangle in javascript:\nfunction area(width, height) {",
    "console.log('Calculating area of rectangle')\n\nfunction area(width, height) {\n    return ",
    "Define area(width, height) in javascript. The function should calculate the rectangle's area. Sure, here is the function: ",
    "Complete the following TypeScript function:\nfunction area(width: number, height: number): number {\n    return ",
    "Write a function to calculate rectangle area in JavaScript using arrow syntax:\nconst area = (width, height) => ",
    "Implement the area function in Java:\npublic static double area(double width, double height) {\n    return ",
    "Write a C++ function that returns the area of a rectangle:\ndouble area(double width, double height) {\n    return ",
    "Complete this Rust function:\nfn area(width: f64, height: f64) -> f64 {\n    ",
    "Write a function in Go that computes the area of a rectangle:\nfunc area(width, height float64) float64 {\n    return ",
    "Implement rectangle area in C#:\npublic static double Area(double width, double height) {\n    return ",
    "Write a Ruby method to calculate the area of a rectangle:\ndef area(width, height)\n  ",
    "Complete the following Kotlin function:\nfun area(width: Double, height: Double): Double {\n    return ",
    "Write a Swift function for rectangle area:\nfunc area(width: Double, height: Double) -> Double {\n    return ",
    "Implement the area function in PHP:\nfunction area($width, $height) {\n    return ",
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
