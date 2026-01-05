from setuptools import setup
import os

lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = f"{lib_folder}/requirements.txt"
install_requires = []
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        install_requires = f.read().splitlines()

setup(
    name="pyastroweatherio",
    packages=["pyastroweatherio"],
    version="0.75.0.dev3",
    license="MIT",
    description="Python Wrapper for OpenMeteo and Met.no REST API",
    long_description=" ".join(
        [
            "Lightweight Python 3 module to receive data via",
            "REST API from OpenMeteo and Met.no and consume",
            "UpTonight reports.",
        ],
    ),
    author="Markus Winkler",
    author_email="winkler.info@icloud.com",
    url="https://github.com/mawinkler/pyastroweatherio",
    keywords=["AstroWeather", "Met.no", "OpenMeteo", "Python"],
    install_requires=install_requires,
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
