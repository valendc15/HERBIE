# src/herbie/framework_helper.py
import shutil
import subprocess
import platform
from typing import Dict, List, Optional
from dataclasses import dataclass
from src.utils.logging_config import setup_logging

logger = setup_logging()


@dataclass
class FrameworkInfo:
    name: str
    commands: List[str]
    check_cmd: str
    dependencies: List[str]
    install_instructions: Dict[str, str]
    project_structure: List[str]
    common_files: List[str]


class FrameworkDatabase:
    """Base de datos de frameworks soportados"""

    FRAMEWORKS = {
        "react": FrameworkInfo(
            name="React",
            commands=["npx create-react-app", "npm create vite@latest"],
            check_cmd="node",
            dependencies=["node", "npm"],
            install_instructions={
                "linux": "sudo apt-get install nodejs npm",
                "darwin": "brew install node",
                "windows": "Descargar desde https://nodejs.org/"
            },
            project_structure=["src/", "public/", "package.json"],
            common_files=["App.js", "index.js", "package.json"]
        ),
        "vue": FrameworkInfo(
            name="Vue.js",
            commands=["npm create vue@latest", "vue create"],
            check_cmd="node",
            dependencies=["node", "npm", "@vue/cli"],
            install_instructions={
                "linux": "sudo apt-get install nodejs npm && npm install -g @vue/cli",
                "darwin": "brew install node && npm install -g @vue/cli",
                "windows": "Descargar Node.js e instalar Vue CLI"
            },
            project_structure=["src/", "public/", "package.json"],
            common_files=["App.vue", "main.js", "package.json"]
        ),
        "django": FrameworkInfo(
            name="Django",
            commands=["django-admin startproject"],
            check_cmd="django-admin",
            dependencies=["python", "pip", "django"],
            install_instructions={
                "linux": "sudo apt-get install python3 python3-pip && pip install django",
                "darwin": "brew install python && pip install django",
                "windows": "Descargar Python e instalar Django con pip"
            },
            project_structure=["manage.py", "requirements.txt", "app/"],
            common_files=["settings.py", "urls.py", "models.py"]
        ),
        "fastapi": FrameworkInfo(
            name="FastAPI",
            commands=["fastapi-cli new"],
            check_cmd="fastapi-cli",
            dependencies=["python", "pip", "fastapi"],
            install_instructions={
                "linux": "pip install fastapi fastapi-cli uvicorn",
                "darwin": "pip install fastapi fastapi-cli uvicorn",
                "windows": "pip install fastapi fastapi-cli uvicorn"
            },
            project_structure=["app/", "requirements.txt"],
            common_files=["main.py", "requirements.txt"]
        ),
        "flutter": FrameworkInfo(
            name="Flutter",
            commands=["flutter create"],
            check_cmd="flutter",
            dependencies=["flutter", "dart"],
            install_instructions={
                "linux": "sudo snap install flutter --classic",
                "darwin": "brew install flutter",
                "windows": "Descargar Flutter SDK"
            },
            project_structure=["lib/", "pubspec.yaml", "android/", "ios/"],
            common_files=["main.dart", "pubspec.yaml"]
        )
    }

    @classmethod
    def get_framework_info(cls, framework: str) -> Optional[FrameworkInfo]:
        return cls.FRAMEWORKS.get(framework.lower())

    @classmethod
    def get_all_frameworks(cls) -> List[str]:
        return list(cls.FRAMEWORKS.keys())


class FrameworkHelper:
    def __init__(self):
        self.system_info = self.get_system_info()
        self.supported_frameworks = FrameworkDatabase.get_all_frameworks()

        logger.info(f"FrameworkHelper inicializado - SO: {self.system_info['os']}")

    def get_system_info(self) -> Dict:
        """Obtiene información del sistema"""
        return {
            "os": platform.system().lower(),
            "version": platform.release(),
            "architecture": platform.machine(),
            "python_version": platform.python_version()
        }

    def check_framework_availability(self, framework: str) -> Dict:
        """Verifica disponibilidad de framework"""

        framework_info = FrameworkDatabase.get_framework_info(framework)
        if not framework_info:
            return {
                "available": False,
                "reason": f"Framework '{framework}' no soportado",
                "supported_frameworks": self.supported_frameworks
            }

        # Verificar comando principal
        if not shutil.which(framework_info.check_cmd):
            return {
                "available": False,
                "reason": f"Comando '{framework_info.check_cmd}' no encontrado",
                "framework_info": framework_info,
                "install_instructions": framework_info.install_instructions.get(
                    self.system_info["os"],
                    "Consulte la documentación oficial"
                )
            }

        return {
            "available": True,
            "framework_info": framework_info,
            "version": self.get_framework_version(framework_info.check_cmd)
        }

    def get_framework_version(self, check_cmd: str) -> str:
        """Obtiene versión del framework"""
        try:
            result = subprocess.run(
                [check_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except:
            return "Desconocida"

    def generate_project_structure(self, framework: str, project_name: str) -> Dict:
        """Genera estructura de proyecto recomendada"""

        framework_info = FrameworkDatabase.get_framework_info(framework)
        if not framework_info:
            return {}

        structure = {
            "project_name": project_name,
            "framework": framework,
            "directories": framework_info.project_structure,
            "files": framework_info.common_files,
            "init_command": f"{framework_info.commands[0]} {project_name}",
            "next_steps": self.get_next_steps(framework)
        }

        return structure

    def get_next_steps(self, framework: str) -> List[str]:
        """Obtiene pasos siguientes después de crear proyecto"""

        next_steps = {
            "react": [
                "cd project_name",
                "npm start",
                "Abrir http://localhost:3000"
            ],
            "vue": [
                "cd project_name",
                "npm run serve",
                "Abrir http://localhost:8080"
            ],
            "django": [
                "cd project_name",
                "python manage.py migrate",
                "python manage.py runserver"
            ],
            "fastapi": [
                "cd project_name",
                "uvicorn app.main:app --reload",
                "Abrir http://localhost:8000"
            ],
            "flutter": [
                "cd project_name",
                "flutter run",
                "Conectar dispositivo o emulador"
            ]
        }

        return next_steps.get(framework, ["Consulte la documentación"])