#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path


def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


setup(
    name="high-speed-playback",
    author="starksimilarity",
    version="0.1a",
    author_email="starksimilarity@gmail.com",
    description="A Python library to replay command line sessions",
    license="GPL",
    packages=find_packages(),
    install_requires=["prompt_toolkit>=2.0", "setuptools"],
    python_requires=">=3.6.0",
    url="https://github.com/starksimilarity/hsp",
    download_url="https://github.com/starksimilarity/hsp/archive/master.zip",
    long_description=read("README.md"),
)
