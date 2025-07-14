# src/herbie/demo/demo_system.py
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from ..agent import HerbieAgent
from ..training.feedback_system import FeedbackDatabase, InteractiveFeedbackCollector
from ..evaluation.evaluator import HerbieEvaluator
from ..utils.logging_config import setup_logging

console = Console()
logger = setup_logging()


class HerbieDemoSystem:
    def __init__(self):
        self.agent = HerbieAgent()
        self.feedback_db = FeedbackDatabase()
        self.feedback_collector = InteractiveFeedbackCollector(self.feedback_db)
        self.evaluator = HerbieEvaluator(self.agent)

        # Casos de demostración
        self.demo_cases = self.load_demo_cases()

        console.print("[bold green]🤖 Sistema de Demostración Herbie Inicializado[/bold green]")

    def load_demo_cases(self) -> List[Dict]:
        """Carga casos de demostración"""

        return [
            {
                'title': "Aplicación React Básica",
                'input': "crea una aplicación React para gestión de tareas",
                'expected': {
                    'framework': 'react',
                    'is_private': False,
                    'difficulty': 'easy'
                },
                'explanation': "Caso básico de detección de framework y generación de proyecto"
            },
            {
                'title': "API Django Privada",
                'input': "necesito un API REST privado con Django para gestión de usuarios",
                'expected': {
                    'framework': 'django',
                    'is_private': True,
                    'difficulty': 'medium'
                },
                'explanation': "Demuestra detección de privacidad y framework backend"
            },
            {
                'title': "App Flutter Compleja",
                'input': "app móvil Flutter privada para fitness tracking con autenticación Firebase",
                'expected': {
                    'framework': 'flutter',
                    'is_private': True,
                    'difficulty': 'hard'
                },
                'explanation': "Caso complejo con múltiples tecnologías y configuración avanzada"
            },
            {
                'title': "Proyecto Vue.js E-commerce",
                'input': "tienda online pública con Vue.js y carrito de compras",
                'expected': {
                    'framework': 'vue',
                    'is_private': False,
                    'difficulty': 'medium'
                },
                'explanation': "Demuestra detección de contexto e-commerce"
            },
            {
                'title': "API FastAPI con Documentación",
                'input': "API FastAPI público para blog con documentación automática",
                'expected': {
                    'framework': 'fastapi',
                    'is_private': False,
                    'difficulty': 'medium'
                },
                'explanation': "Muestra capacidad de entender requerimientos específicos"
            }
        ]

    def run_interactive_demo(self):
        """Ejecuta demostración interactiva"""

        console.print(Panel.fit(
            "[bold cyan]🎯 DEMOSTRACIÓN INTERACTIVA - HERBIE AGENT[/bold cyan]\n\n"
            "Selecciona una opción:\n"
            "[1] Demostración guiada\n"
            "[2] Prueba personalizada\n"
            "[3] Evaluación completa\n"
            "[4] Estadísticas del sistema\n"
            "[5] Entrenamiento en vivo\n"
            "[0] Salir"
        ))

        while True:
            choice = console.input("\n🔹 Selecciona opción: ")

            if choice == "1":
                self.run_guided_demo()
            elif choice == "2":
                self.run_custom_test()
            elif choice == "3":
                self.run_complete_evaluation()
            elif choice == "4":
                self.show_system_stats()
            elif choice == "5":
                self.run_live_training()
            elif choice == "0":
                console.print("[bold red]👋 ¡Hasta luego![/bold red]")
                break
            else:
                console.print("[bold red]❌ Opción inválida[/bold red]")

    def run_guided_demo(self):
        """Ejecuta demostración guiada"""

        console.print(Panel.fit(
            "[bold green]🎯 DEMOSTRACIÓN GUIADA[/bold green]\n\n"
            f"Se ejecutarán {len(self.demo_cases)} casos de prueba predefinidos"
        ))

        for i, demo_case in enumerate(self.demo_cases, 1):
            console.print(f"\n[bold cyan]📋 Caso {i}/{len(self.demo_cases)}: {demo_case['title']}[/bold cyan]")
            console.print(f"[dim]{demo_case['explanation']}[/dim]")

            # Mostrar input
            console.print(f"\n[bold]Input:[/bold] {demo_case['input']}")

            # Ejecutar procesamiento
            with Progress() as progress:
                task = progress.add_task("Procesando...", total=100)

                start_time = time.time()
                response = self.agent.process_request(demo_case['input'])
                end_time = time.time()

                progress.update(task, completed=100)

            # Mostrar resultado
            self.display_response(response, end_time - start_time)

            # Verificar expectativas
            self.verify_expectations(response, demo_case['expected'])

            # Pausa para revisión
            if i < len(self.demo_cases):
                console.input("\n[dim]Presiona Enter para continuar...[/dim]")

    def run_custom_test(self):
        """Ejecuta prueba personalizada"""

        console.print(Panel.fit(
            "[bold green]🔧 PRUEBA PERSONALIZADA[/bold green]\n\n"
            "Ingresa tu propio comando para ver cómo lo procesa Herbie"
        ))

        while True:
            user_input = console.input("\n[bold]Tu comando:[/bold] ")

            if user_input.lower() in ['salir', 'exit', 'quit']:
                break

            if not user_input.strip():
                console.print("[bold red]❌ Por favor, ingresa un comando válido[/bold red]")
                continue

            # Procesar comando
            start_time = time.time()
            response = self.agent.process_request(user_input)
            end_time = time.time()

            # Mostrar resultado
            self.display_response(response, end_time - start_time)

            # Recopilar feedback
            collect_feedback = console.input("\n[dim]¿Quieres proporcionar feedback? (s/n): [/dim]")
            if collect_feedback.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                self.feedback_collector.collect_feedback(
                    user_id="demo_user",
                    user_input=user_input,
                    agent_response=json.dumps(response.result) if response.result else str(response.error),
                    response_time=end_time - start_time
                )

    def display_response(self, response, response_time: float):
        """Muestra respuesta del agente"""

        if response.success:
            # Crear tabla con resultado
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Campo", style="cyan")
            table.add_column("Valor", style="green")

            for key, value in response.result.items():
                table.add_row(key, str(value))

            console.print(table)

            # Mostrar métricas
            console.print(f"\n[bold]Métricas:[/bold]")
            console.print(f"⏱️  Tiempo: {response_time:.2f}s")
            console.print(f"🎯 Confianza: {response.confidence:.2%}")

            # Mostrar razonamiento si está disponible
            if response.reasoning:
                console.print(Panel(
                    response.reasoning,
                    title="💭 Razonamiento",
                    border_style="blue"
                ))
        else:
            console.print(Panel(
                f"[bold red]❌ Error: {response.error}[/bold red]",
                border_style="red"
            ))

    def verify_expectations(self, response, expected: Dict):
        """Verifica si la respuesta cumple expectativas"""

        if not response.success:
            console.print("[bold red]❌ FALLO - Error en procesamiento[/bold red]")
            return

        result = response.result
        checks = []

        # Verificar framework
        if 'framework' in expected:
            if result.get('framework') == expected['framework']:
                checks.append("✅ Framework correcto")
            else:
                checks.append(
                    f"❌ Framework incorrecto: esperado {expected['framework']}, obtenido {result.get('framework')}")

        # Verificar privacidad
        if 'is_private' in expected:
            if result.get('is_private') == expected['is_private']:
                checks.append("✅ Privacidad correcta")
            else:
                checks.append(
                    f"❌ Privacidad incorrecta: esperado {expected['is_private']}, obtenido {result.get('is_private')}")

        # Mostrar verificación
        console.print("\n[bold]Verificación:[/bold]")
        for check in checks:
            console.print(f"  {check}")

    def run_complete_evaluation(self):
        """Ejecuta evaluación completa"""

        console.print(Panel.fit(
            "[bold green]📊 EVALUACIÓN COMPLETA[/bold green]\n\n"
            "Ejecutando evaluación integral del sistema..."
        ))

        # Preparar casos de prueba
        test_cases = []
        for demo_case in self.demo_cases:
            test_cases.append({
                'input': demo_case['input'],
                'expected': demo_case['expected']
            })

        # Ejecutar evaluación
        with Progress() as progress:
            task = progress.add_task("Evaluando...", total=len(test_cases))

            results = self.evaluator.run_comprehensive_evaluation(test_cases)

            progress.update(task, completed=len(test_cases))

        # Mostrar resultados
        self.display_evaluation_results(results)

        # Generar reporte
        report = self.evaluator.generate_evaluation_report(results)

        # Guardar reporte
        report_path = f"reports/evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        console.print(f"\n[bold green]📄 Reporte guardado en: {report_path}[/bold green]")

    def display_evaluation_results(self, results: Dict):
        """Muestra resultados de evaluación"""

        # Score general
        console.print(Panel.fit(
            f"[bold green]🎯 SCORE GENERAL: {results['overall_score']:.2%}[/bold green]",
            border_style="green"
        ))

        # Tabla de métricas
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Categoría", style="cyan")
        table.add_column("Métrica", style="yellow")
        table.add_column("Valor", style="green")

        # Parsing accuracy
        parsing = results['parsing_accuracy']
        table.add_row("Parsing", "Framework", f"{parsing['framework_accuracy']:.2%}")
        table.add_row("", "Privacidad", f"{parsing['privacy_accuracy']:.2%}")
        table.add_row("", "Naming", f"{parsing['naming_accuracy']:.2%}")

        # Response quality
        quality = results['response_quality']
        table.add_row("Calidad", "Claridad", f"{quality['avg_clarity']:.2%}")
        table.add_row("", "Completitud", f"{quality['avg_completeness']:.2%}")
        table.add_row("", "Consistencia", f"{quality['avg_consistency']:.2%}")

        # Performance
        performance = results['performance_metrics']
        table.add_row("Rendimiento", "Tiempo Promedio", f"{performance['avg_response_time']:.2f}s")
        table.add_row("", "Confianza", f"{performance['avg_confidence']:.2%}")

        console.print(table)

    def show_system_stats(self):
        """Muestra estadísticas del sistema"""

        console.print(Panel.fit(
            "[bold green]📈 ESTADÍSTICAS DEL SISTEMA[/bold green]"
        ))

        # Estadísticas de feedback
        feedback_stats = self.feedback_db.get_statistics()

        # Estadísticas de few-shot
        few_shot_stats = self.agent.few_shot_manager.get_statistics()

        # Mostrar estadísticas
        stats_table = Table(show_header=True, header_style="bold magenta")
        stats_table.add_column("Categoría", style="cyan")
        stats_table.add_column("Métrica", style="yellow")
        stats_table.add_column("Valor", style="green")

        # Feedback
        stats_table.add_row("Feedback", "Total", str(feedback_stats.get('total_feedback', 0)))
        stats_table.add_row("", "Rating Promedio", f"{feedback_stats.get('avg_rating', 0):.2f}/5")
        stats_table.add_row("", "Tasa de Éxito", f"{feedback_stats.get('success_rate', 0):.1f}%")

        # Few-shot
        stats_table.add_row("Few-Shot", "Ejemplos", str(few_shot_stats.get('total_examples', 0)))
        stats_table.add_row("", "Éxito Promedio", f"{few_shot_stats.get('avg_success_rate', 0):.2%}")

        console.print(stats_table)

        # Distribución por framework
        if feedback_stats.get('framework_distribution'):
            console.print("\n[bold]Distribución por Framework:[/bold]")
            for framework, count in feedback_stats['framework_distribution'].items():
                console.print(f"  {framework}: {count}")

    def run_live_training(self):
        """Ejecuta entrenamiento en vivo"""

        console.print(Panel.fit(
            "[bold green]🎓 ENTRENAMIENTO EN VIVO[/bold green]\n\n"
            "Demostración del proceso de aprendizaje del agente"
        ))

        # Verificar datos de entrenamiento
        feedback_stats = self.feedback_db.get_statistics()

        if feedback_stats.get('total_feedback', 0) < 10:
            console.print("[bold yellow]⚠️  Pocos datos de feedback para entrenamiento significativo[/bold yellow]")
            console.print("Recomendación: Recopilar más feedback antes de entrenar")
            return

        # Entrenar modelo de reward
        try:
            from ..training.feedback_system import RewardModelTrainer

            console.print("🔄 Entrenando modelo de reward...")

            trainer = RewardModelTrainer(self.feedback_db)

            with Progress() as progress:
                task = progress.add_task("Entrenando...", total=100)

                results = trainer.train_model()

                progress.update(task, completed=100)

            # Mostrar resultados
            console.print(f"\n[bold green]✅ Entrenamiento completado[/bold green]")
            console.print(f"R² Score: {results['r2']:.3f}")
            console.print(f"MSE: {results['mse']:.3f}")
            console.print(f"MAE: {results['mae']:.3f}")

            # Mostrar feature importance
            console.print("\n[bold]Importancia de Features:[/bold]")
            for feature, importance in sorted(results['feature_importance'].items(),
                                              key=lambda x: x[1], reverse=True)[:5]:
                console.print(f"  {feature}: {importance:.3f}")

            # Guardar modelo
            model_path = f"models/reward_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.joblib"
            trainer.save_model(model_path)

            console.print(f"\n[bold green]💾 Modelo guardado en: {model_path}[/bold green]")

        except Exception as e:
            console.print(f"[bold red]❌ Error en entrenamiento: {str(e)}[/bold red]")
            logger.error(f"Error en entrenamiento: {e}")


if __name__ == "__main__":
    demo = HerbieDemoSystem()
    demo.run_interactive_demo()