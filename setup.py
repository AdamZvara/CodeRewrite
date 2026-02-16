from setuptools import setup, find_packages

setup(
    name="coderewrite",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "EasyEdit @ git+https://github.com/AdamZvara/EasyEdit.git@main",
        "torch>=2.9",
        "transformers>=4.57",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4",
            "flake8>=6.1",
            "pre-commit>=3.3"
        ]
    },
    python_requires=">=3.10",
)