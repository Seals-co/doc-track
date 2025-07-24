from pathlib import Path

from setuptools import find_packages, setup

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
    name="doc-track",
    version="0.1.3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "pyyaml==6.0.2",
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
