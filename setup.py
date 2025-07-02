from setuptools import find_packages, setup

setup(
    name="doc-track",
    version="0.1.2",
    packages=find_packages(),
    install_requires=[
        "iniconfig==2.1.0",
        "packaging==25.0",
        "pluggy==1.6.0",
        "Pygments==2.19.1",
        "pytest==8.4.1",
        "setuptools==80.9.0",
        "tree-sitter==0.24.0",
        "tree-sitter-python==0.23.6",
        "pyyaml==6.0.2",
        "ruff==0.12.1",
    ],
    entry_points={
        "console_scripts": [
            "doc-track = doctrack.cli:main",
        ],
    },
    python_requires=">=3.7",
    author="Ratinax",
    description="Command that helps keeping track of piece of code marked as 'documented'",
    url="https://github.com/Seals-co/doc-track/",
    project_urls={
        "Source": "https://github.com/Seals-co/doc-track/",
        "Tracker": "https://github.com/Seals-co/doc-track/issues/",
    },
)
