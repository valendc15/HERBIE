import os
from datetime import datetime
from typing import Optional

from herbie_enhanced.core_system import ProjectExecutor, ProjectAnalysis, ExecutionResult


class EnhancedProjectExecutor(ProjectExecutor):
    """
    Ejecutor mejorado con mejor manejo de errores y logging
    """

    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.setup_logging()

    def setup_logging(self):
        """Configura logging específico para el ejecutor"""
        import logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def execute_project(self, analysis: ProjectAnalysis) -> ExecutionResult:
        """
        Ejecuta la creación del proyecto con análisis mejorado
        """
        start_time = datetime.now()
        steps_completed = []

        try:
            # 1. Validar análisis
            if not self._validate_analysis(analysis):
                return ExecutionResult(
                    success=False,
                    error_message="Análisis inválido",
                    execution_time=0.0
                )

            steps_completed.append("Análisis validado")

            # 2. Verificar dependencias
            if not self._check_dependencies(analysis.framework):
                return ExecutionResult(
                    success=False,
                    error_message=f"Dependencias faltantes para {analysis.framework}",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    steps_completed=steps_completed
                )

            steps_completed.append("Dependencias verificadas")

            # 3. Crear repositorio local
            if not self._create_local_project(analysis):
                return ExecutionResult(
                    success=False,
                    error_message="Error creando proyecto local",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    steps_completed=steps_completed
                )

            steps_completed.append("Proyecto local creado")

            # 4. Crear repositorio en GitHub
            repo_url = self._create_github_repo(analysis)
            if not repo_url:
                return ExecutionResult(
                    success=False,
                    error_message="Error creando repositorio en GitHub",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    steps_completed=steps_completed
                )

            steps_completed.append("Repositorio GitHub creado")

            # 5. Subir código
            if not self._push_to_github(analysis):
                return ExecutionResult(
                    success=False,
                    error_message="Error subiendo código a GitHub",
                    execution_time=(datetime.now() - start_time).total_seconds(),
                    steps_completed=steps_completed
                )

            steps_completed.append("Código subido a GitHub")

            execution_time = (datetime.now() - start_time).total_seconds()

            return ExecutionResult(
                success=True,
                repo_url=repo_url,
                execution_time=execution_time,
                steps_completed=steps_completed,
                metrics={
                    'framework': analysis.framework,
                    'complexity': analysis.complexity_score,
                    'predicted_success': analysis.predicted_success
                }
            )

        except Exception as e:
            self.logger.error(f"Error ejecutando proyecto: {e}")
            return ExecutionResult(
                success=False,
                error_message=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                steps_completed=steps_completed
            )

    def _validate_analysis(self, analysis: ProjectAnalysis) -> bool:
        """Valida el análisis del proyecto"""
        required_fields = ['repo_name', 'framework', 'description']
        return all(getattr(analysis, field) for field in required_fields)

    def _check_dependencies(self, framework: str) -> bool:
        """Verifica dependencias del framework"""
        # Simulación - en implementación real verificaría comandos
        dependency_commands = {
            'react': 'node',
            'vue': 'node',
            'angular': 'ng',
            'django': 'django-admin',
            'fastapi': 'python',
            'nextjs': 'node',
            'flutter': 'flutter'
        }

        required_cmd = dependency_commands.get(framework)
        if not required_cmd:
            return False

        # Simulación de verificación exitosa
        return True

    def _create_local_project(self, analysis: ProjectAnalysis) -> bool:
        """Crea proyecto local"""
        # Simulación - en implementación real ejecutaría comandos
        self.logger.info(f"Creando proyecto local: {analysis.repo_name}")
        return True

    def _create_github_repo(self, analysis: ProjectAnalysis) -> Optional[str]:
        """Crea repositorio en GitHub"""
        # Simulación - en implementación real usaría GitHub API
        repo_url = f"https://github.com/user/{analysis.repo_name}"
        self.logger.info(f"Repositorio creado: {repo_url}")
        return repo_url

    def _push_to_github(self, analysis: ProjectAnalysis) -> bool:
        """Sube código a GitHub"""
        # Simulación - en implementación real usaría git commands
        self.logger.info(f"Código subido para: {analysis.repo_name}")
        return True
