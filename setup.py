from setuptools import find_packages, setup


def parse_requirements(filename):
    with open(filename) as f:
        lines = f.read().splitlines()

    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


setup(
    name="doc-track",
    version="0.1.1",
    packages=find_packages(),
    install_requires=parse_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "doc-track = doctrack.cli:main",
        ],
    },
    python_requires=">=3.7",
    author="Ratinax",
    description="Command that helps keeping track of piece of code marked as 'documented'",
)
