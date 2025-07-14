"""
Setup configuration for Herbie Agent
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="herbie-agent",
    version="1.0.0",
    author="Tu Nombre",
    author_email="tu.email@universidad.edu",
    description="Asistente inteligente para creación de repositorios GitHub",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tu-usuario/herbie-agent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "herbie=herbie.cli:app",
        ],
    },
    include_package_data=True,
    package_data={
        "herbie": ["data/*.json", "configs/*.yaml"],
    },
    extras_require={
        "dev": [
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
            "pre-commit>=3.4.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.2.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    zip_safe=False,
)