from setuptools import setup

setup(
    name="pyastroweatherio",
    packages=["pyastroweatherio"],
    version="0.22.3",
    license="MIT",
    description="Python Wrapper for 7Timer REST API",
    long_description=" ".join(
        ["Lightweight Python 3 module to receive data via", "REST API from 7Timer."],
    ),
    author="Markus Winkler",
    author_email="winkler.info@icloud.com",
    url="https://github.com/mawinkler/pyastroweatherio",
    keywords=["AstroWeather", "7Timer", "Python"],
    install_requires=["aiohttp", "pyephem"],
    classifiers=[
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
