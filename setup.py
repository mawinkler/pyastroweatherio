from setuptools import setup

setup(
    name="pyastroweatherio",
    packages=["pyastroweatherio"],
    version="0.62.0.dev1",
    license="MIT",
    description="Python Wrapper for 7Timer and Met.no REST API",
    long_description=" ".join(
        [
            "Lightweight Python 3 module to receive data via",
            "REST API from 7Timer and Met.no and consume",
            "UpTonight reports.",
        ],
    ),
    author="Markus Winkler",
    author_email="winkler.info@icloud.com",
    url="https://github.com/mawinkler/pyastroweatherio",
    keywords=["AstroWeather", "7Timer", "Met.no", "Python"],
    install_requires=["aiohttp", "aiofiles", "pyephem"],
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
