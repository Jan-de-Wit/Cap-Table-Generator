"""
Setup configuration for Cap Table Generator
Allows installing the package in development mode for testing.
"""

from setuptools import setup, find_packages

setup(
    name="captable-generator",
    version="1.0.0",
    description="Cap Table Generator - JSON to Excel with formula linking",
    author="Cap Table Generator Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "xlsxwriter>=3.1.0",
        "jsonschema>=4.19.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-timeout>=2.1.0",
            "openpyxl>=3.1.0",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)

