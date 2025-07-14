# src/herbie/github_client.py
import requests
import subprocess
import os
from typing import Dict, Optional, List
from src.utils.logging_config import setup_logging

logger = setup_logging()


class GitHubClient:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"

        if not self.token:
            logger.warning("GITHUB_TOKEN no configurado")

        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

        self.username = self.get_username()
        logger.info(f"GitHub Client inicializado - Usuario: {self.username}")

    def get_username(self) -> str:
        """Obtiene nombre de usuario"""
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers)
            if response.status_code == 200:
                return response.json().get('login', 'unknown')
            return 'unknown'
        except Exception as e:
            logger.error(f"Error obteniendo usuario: {e}")
            return 'unknown'

    def create_repository(self, repo_config: Dict) -> Dict:
        """Crea repositorio en GitHub"""

        url = f"{self.base_url}/user/repos"

        payload = {
            "name": repo_config['name'],
            "description": repo_config.get('description', ''),
            "private": repo_config.get('private', False),
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True,
            "auto_init": False
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)

            if response.status_code == 201:
                repo_data = response.json()
                logger.info(f"Repositorio '{repo_config['name']}' creado exitosamente")

                return {
                    "success": True,
                    "repo_url": repo_data['html_url'],
                    "clone_url": repo_data['clone_url'],
                    "ssh_url": repo_data['ssh_url'],
                    "repo_data": repo_data
                }
            else:
                logger.error(f"Error creando repositorio: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except Exception as e:
            logger.error(f"Excepción creando repositorio: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def push_project(self, project_path: str, repo_name: str) -> Dict:
        """Sube proyecto local a GitHub"""

        try:
            original_dir = os.getcwd()
            os.chdir(project_path)

            # Comandos git
            commands = [
                ["git", "init"],
                ["git", "add", "."],
                ["git", "commit", "-m", "Initial commit by Herbie Agent"],
                ["git", "branch", "-M", "main"],
                ["git", "remote", "add", "origin", f"https://github.com/{self.username}/{repo_name}.git"],
                ["git", "push", "-u", "origin", "main"]
            ]

            for cmd in commands:
                logger.info(f"Ejecutando: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if result.returncode != 0:
                    logger.error(f"Error en comando git: {result.stderr}")
                    return {
                        "success": False,
                        "error": f"Git error: {result.stderr}"
                    }

            os.chdir(original_dir)

            logger.info(f"Proyecto subido exitosamente a GitHub")
            return {"success": True}

        except Exception as e:
            os.chdir(original_dir)
            logger.error(f"Error subiendo proyecto: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def check_repository_exists(self, repo_name: str) -> bool:
        """Verifica si repositorio existe"""
        try:
            url = f"{self.base_url}/repos/{self.username}/{repo_name}"
            response = requests.get(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False

    def get_repository_info(self, repo_name: str) -> Optional[Dict]:
        """Obtiene información del repositorio"""
        try:
            url = f"{self.base_url}/repos/{self.username}/{repo_name}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None