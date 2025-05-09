from setuptools import setup, find_packages

setup(
    name="tg_bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiogram>=3.0.0",
        "httpx>=0.24.0",
        "redis>=4.5.0",
    ],
    python_requires=">=3.8",
) 