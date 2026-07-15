#!/usr/bin/env python3
"""
GMD v1.0.0 - Git Merge Directories Suite
Directory synchronization and git submodule management tools.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gmd-tools",
    version="1.0.0",
    author="w4d4f4k",
    author_email="w4d4f4k@gmail.com",
    description="Git Merge Directories - Directory sync and git submodule management suite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/w4d4f4k/gmd",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    install_requires=[
        "rich>=13.0.0",
        "pydantic>=2.0.0",
        "PyYAML>=6.0",
        "click>=8.0.0",
    ],
    extras_require={
        "gui": [
            "Pillow>=9.0.0",  # Optional for advanced icon support
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gmd-merge=gmd.cli.merge:main",
            "gmd-commit=gmd.cli.commit:main",
            "gmd-gui=gmd.gui.main:main",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gmd-merge=gmd.cli.merge:main",
            "gmd-commit=gmd.cli.commit:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
