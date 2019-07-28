from setuptools import setup, find_packages


NAME = "anisole"
DESCRIPTION = "Anime management all in one."
URL = "https://github.com/wooddance/anisole"
EMAIL = "zireael.me@gmail.com"
AUTHOR = "wooddance"
VERSION = "0.0.1"

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=open("README.md").read(),
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    python_requires=">=3.6.0",
    install_requires=open("requirements.txt").read().splitlines(),
    packages=find_packages(exclude=["tests", "docs"]),
    entry_points={"console_scripts": ["bgm=anisole.bgm.cli:bgm"]},
)
