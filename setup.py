"""Setup script for RadarDOU SDK."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="radardou",
    version="1.0.0",
    author="Radar DOU",
    author_email="suporte@radar-dou.com",
    description="SDK oficial para a API do Radar DOU - Monitoramento do Diário Oficial da União",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/radar-dou/radardou-python",
    project_urls={
        "Documentation": "https://radar-dou.com/docs",
        "API Reference": "https://radar-dou.com/api-keys",
        "Bug Reports": "https://github.com/radar-dou/radardou-python/issues",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "types-requests>=2.28.0",
        ],
    },
    keywords=[
        "dou",
        "diario-oficial",
        "brasil",
        "governo",
        "api",
        "sdk",
        "radar-dou",
        "monitoramento",
        "licitacao",
        "publicacao"
    ],
)
