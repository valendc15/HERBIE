"""
Interfaz de línea de comandos para Herbie Agent
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from pathlib import Path

from src.agent import HerbieAgent
from .demo.demo_system import HerbieDemoSystem

app = typer.Typer(help="Herbie Agent - Asistente para creación de repositorios GitHub")
console = Console()


@app.command()
def create(
        command: str = typer.Argument(..., help="Comando para crear proyecto"),
        mode: str = typer.Option("few_shot", help="Modo de aprendizaje"),
        user_id: str = typer.Option("cli_user", help="ID del usuario"),
        full: bool = typer.Option(False, help="Crear proyecto completo (incluyendo GitHub)"),
        verbose: bool = typer.Option(False, help="Mostrar información detallada")
):
    """Crear proyecto basado en comando de texto"""

    console.print(f"🤖 [bold green]Procesando:[/bold green] {command}")

    try:
        agent = HerbieAgent()
        agent.set_learning_mode(mode)

        if full:
            # Crear proyecto completo
            with Progress() as progress:
                task = progress.add_task("Creando proyecto completo...", total=100)

                result = agent.create_full_project(command, user_id)

                progress.update(task, completed=100)

            if result['success']:
                console.print(Panel.fit(
                    f"✅ [bold green]Proyecto creado exitosamente![/bold green]\n"
                    f"🔗 URL: {result['repo_url']}\n"
                    f"📁 Nombre: {result['project_info'].repo_name}\n"
                    f"🔧 Framework: {result['project_info'].framework}",
                    border_style="green"
                ))
            else:
                console.print(Panel.fit(
                    f"❌ [bold red]Error en {result['step']}:[/bold red]\n"
                    f"{result['error']}",
                    border_style="red"
                ))
        else:
            # Solo procesamiento
            response = agent.process_request(command, user_id)

            if response.success:
                # Mostrar resultado en tabla
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Campo", style="cyan")
                table.add_column("Valor", style="green")

                for key, value in response.result.items():
                    table.add_row(key, str(value))

                console.print(table)

                if verbose:
                    console.print(Panel(
                        f"⏱️ Tiempo: {response.response_time:.2f}s\n"
                        f"🎯 Confianza: {response.confidence:.2%}\n"
                        f"🧠 Modo: {mode}",
                        title="Métricas",
                        border_style="blue"
                    ))

                    if response.reasoning:
                        console.print(Panel(
                            response.reasoning,
                            title="Razonamiento",
                            border_style="yellow"
                        ))
            else:
                console.print(Panel.fit(
                    f"❌ [bold red]Error:[/bold red] {response.error}",
                    border_style="red"
                ))

    except Exception as e:
        console.print(f"❌ [bold red]Error:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def demo():
    """Ejecutar demostración interactiva"""

    console.print("🎯 [bold green]Iniciando demostración interactiva...[/bold green]")

    try:
        demo_system = HerbieDemoSystem()
        demo_system.run_interactive_demo()

    except KeyboardInterrupt:
        console.print("\n👋 [bold yellow]Demostración cancelada[/bold yellow]")
    except Exception as e:
        console.print(f"❌ [bold red]Error en demostración:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def evaluate(
        test_file: Optional[str] = typer.Option(None, help="Archivo con casos de prueba"),
        output: Optional[str] = typer.Option(None, help="Archivo de salida para resultados")
):
    """Ejecutar evaluación del sistema"""

    console.print("📊 [bold green]Ejecutando evaluación...[/bold green]")

    try:
        from .evaluation.evaluator import HerbieEvaluator

        agent = HerbieAgent()
        evaluator = HerbieEvaluator(agent)

        # Cargar casos de prueba
        if test_file:
            with open(test_file, 'r', encoding='utf-8') as f:
                test_cases = json.load(f)
        else:
            # Casos por defecto
            test_cases = [
                {
                    'input': "crea una aplicación React para gestión de tareas",
                    'expected': {'framework': 'react', 'is_private': False}
                },
                {
                    'input': "API Django privado para usuarios",
                    'expected': {'framework': 'django', 'is_private': True}
                }
            ]

        # Ejecutar evaluación
        with Progress() as progress:
            task = progress.add_task("Evaluando...", total=len(test_cases))

            results = evaluator.run_comprehensive_evaluation(test_cases)

            progress.update(task, completed=len(test_cases))

        # Mostrar resultados
        console.print(Panel.fit(
            f"🎯 [bold green]Score General: {results['overall_score']:.2%}[/bold green]",
            border_style="green"
        ))

        # Guardar resultados
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            console.print(f"📄 Resultados guardados en: {output}")

    except Exception as e:
        console.print(f"❌ [bold red]Error en evaluación:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def train(
        mode: str = typer.Option("few_shot", help="Modo de entrenamiento"),
        data_path: Optional[str] = typer.Option(None, help="Ruta a datos de entrenamiento")
):
    """Entrenar modelos del sistema"""

    console.print(f"🎓 [bold green]Entrenando modelo ({mode})...[/bold green]")

    try:
        if mode == "few_shot":
            from .training.few_shot_manager import FewShotManager

            manager = FewShotManager()
            stats = manager.get_statistics()

            console.print(f"📊 Ejemplos disponibles: {stats['total_examples']}")
            console.print(f"🎯 Tasa de éxito promedio: {stats['avg_success_rate']:.2%}")

        elif mode == "rlhf":
            from .training.feedback_system import RewardModelTrainer, FeedbackDatabase

            feedback_db = FeedbackDatabase()
            trainer = RewardModelTrainer(feedback_db)

            with Progress() as progress:
                task = progress.add_task("Entrenando modelo de reward...", total=100)

                results = trainer.train_model()

                progress.update(task, completed=100)

            console.print(f"✅ Modelo entrenado - R²: {results['r2']:.3f}")

        else:
            console.print(f"❌ Modo de entrenamiento no soportado: {mode}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"❌ [bold red]Error en entrenamiento:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def stats():
    """Mostrar estadísticas del sistema"""

    console.print("📈 [bold green]Estadísticas del Sistema[/bold green]")

    try:
        from .training.feedback_system import FeedbackDatabase
        from .training.few_shot_manager import FewShotManager

        # Estadísticas de feedback
        feedback_db = FeedbackDatabase()
        feedback_stats = feedback_db.get_statistics()

        # Estadísticas de few-shot
        few_shot_manager = FewShotManager()
        few_shot_stats = few_shot_manager.get_statistics()

        # Mostrar en tabla
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Categoría", style="cyan")
        table.add_column("Métrica", style="yellow")
        table.add_column("Valor", style="green")

        # Feedback
        table.add_row("Feedback", "Total", str(feedback_stats.get('total_feedback', 0)))
        table.add_row("", "Rating Promedio", f"{feedback_stats.get('avg_rating', 0):.2f}/5")
        table.add_row("", "Tasa de Éxito", f"{feedback_stats.get('success_rate', 0):.1f}%")

        # Few-shot
        table.add_row("Few-Shot", "Ejemplos", str(few_shot_stats.get('total_examples', 0)))
        table.add_row("", "Éxito Promedio", f"{few_shot_stats.get('avg_success_rate', 0):.2%}")

        console.print(table)

    except Exception as e:
        console.print(f"❌ [bold red]Error obteniendo estadísticas:[/bold red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def config(
        show: bool = typer.Option(False, help="Mostrar configuración actual"),
        set_key: Optional[str] = typer.Option(None, help="Clave a configurar"),
        set_value: Optional[str] = typer.Option(None, help="Valor a configurar")
):
    """Configurar sistema"""

    config_file = Path("configs/user_config.json")

    if show:
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
            console.print(json.dumps(config, indent=2))
        else:
            console.print("No hay configuración guardada")

    elif set_key and set_value:
        config = {}
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)

        config[set_key] = set_value

        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        console.print(f"✅ Configurado {set_key} = {set_value}")

    else:
        console.print("Usa --show para ver configuración o --set-key/--set-value para configurar")


if __name__ == "__main__":
    app()