from setuptools import setup, find_packages

setup(
    name="stealth-axiom",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "stealth-axiom=stealth_axiom.client:main",
        ],
    },
    python_requires=">=3.10",
)
