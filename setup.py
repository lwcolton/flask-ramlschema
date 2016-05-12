from setuptools import setup, find_packages
from codecs import open
import os

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "version"), "r") as version_handle:
    version = version_handle.read().strip()

setup(
    name = "flask-ramlschema",
    version = version,
    description = "Framework for HTTP API's using RAML and Flask",
    url = "https://github.com/lwcolton/flask-ramlschema",
    author = "Colton Leekley-Winslow",
    author_email = "colton@hurricanelabs.com",
    packages=find_packages(exclude=['tests']),
    install_requires = ["flask", "jsonschema", "pymongo", "pyyaml"],
)



