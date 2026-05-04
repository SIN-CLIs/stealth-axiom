from setuptools import setup, find_packages

setup(
    name="stealth-axiom",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
    ],
    extras_require={
        "test": ["pytest>=8.0", "pytest-mock"],
    },
    entry_points={
        "console_scripts": [
            "stealth-axiom=stealth_axiom.client:main",
        ],
    },
    python_requires=">=3.10",
)
