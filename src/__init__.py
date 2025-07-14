"""
Herbie Agent - Asistente Inteligente para Creación de Repositorios
"""

__version__ = "2.0.0"
__author__ = "Valentino Di Capua"
__email__ = "valentino.dicapua@ing.austral.edu.ar"
__description__ = "Agente inteligente para automatizar creación de repositorios GitHub (H.E.R.B.I.E. Helpful Engine for Repository Building and Intelligent Execution)"

from .agent import HerbieAgent
from .framework_helper import FrameworkHelper
from .github_client import GitHubClient

__all__ = [
    "HerbieAgent",
    "FrameworkHelper",
    "GitHubClient"
]