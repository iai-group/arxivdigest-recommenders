from setuptools import setup, find_packages

with open("requirements.txt") as file:
    install_requires = file.read().splitlines()

setup(
    name="arxivdigest_recommenders",
    author="Olaf Liadal",
    packages=find_packages(),
    install_requires=install_requires,
)
