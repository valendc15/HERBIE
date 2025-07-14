# src/herbie/training/cot_processor.py
import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..utils.logging_config import setup_logging

logger = setup_logging()


@dataclass
class ReasoningStep:
    step_number: int
    title: str
    reasoning: str
    result: str
    confidence: float


@dataclass
class CoTResponse:
    reasoning_steps: List[ReasoningStep]
    final_result: Dict
    overall_confidence: float
    raw_response: str


class ChainOfThoughtProcessor:
    def __init__(self, llm):
        self.llm = llm
        self.reasoning_steps = [
            "identificar_framework",
            "determinar_visibilidad",
            "generar_nombre",
            "crear_descripcion",
            "configurar_comando"
        ]

        logger.info("ChainOfThoughtProcessor inicializado")

    def create_cot_prompt(self, user_input: str) -> str:
        """Crea prompt con razonamiento paso a paso"""

        prompt = f"""
Eres un experto en desarrollo de software. Analiza este comando paso a paso usando razonamiento explícito.

Input del usuario: "{user_input}"

Sigue estos pasos de razonamiento:

PASO 1: Identificar Framework
- Analiza el texto buscando palabras clave de frameworks
- Frameworks disponibles: react, vue, angular, django, fastapi, flask, rails, flutter
- Si no es explícito, infiere del contexto
- Razonamiento: [Explica tu proceso de pensamiento]
- Resultado: [Framework identificado]

PASO 2: Determinar Visibilidad del Repositorio
- Busca indicadores de privacidad: "privado", "público", "private", "public"
- Considera el contexto del proyecto
- Por defecto usar "público" si no se especifica
- Razonamiento: [Explica tu decisión]
- Resultado: [true/false]

PASO 3: Generar Nombre del Repositorio
- Extrae conceptos clave del proyecto
- Convierte a formato kebab-case
- Evita palabras genéricas como "app", "sistema"
- Debe ser descriptivo pero conciso
- Razonamiento: [Explica la construcción del nombre]
- Resultado: [nombre-del-repo]

PASO 4: Crear Descripción
- Combina framework + propósito del proyecto
- Usa terminología técnica apropiada
- Debe ser clara y profesional
- Razonamiento: [Explica la construcción de la descripción]
- Resultado: [descripción completa]

PASO 5: Configurar Comando de Inicialización
- Usa el comando estándar para el framework
- Incluye el nombre del proyecto
- Considera configuraciones adicionales si es necesario
- Razonamiento: [Explica la selección del comando]
- Resultado: [comando completo]

Realiza el análisis paso a paso:

[Espacio para el razonamiento completo]

RESULTADO FINAL JSON:
{{
  "repo_name": "nombre-generado",
  "framework": "framework-identificado",
  "is_private": true/false,
  "description": "descripción generada",
  "init_command": "comando generado"
}}
"""

        return prompt

    def process_cot_response(self, response: str) -> CoTResponse:
        """Procesa respuesta CoT y extrae información"""

        try:
            # Extraer pasos de razonamiento
            reasoning_steps = self.extract_reasoning_steps(response)

            # Extraer resultado final
            final_result = self.extract_final_json(response)

            # Calcular confianza general
            overall_confidence = self.calculate_overall_confidence(reasoning_steps)

            return CoTResponse(
                reasoning_steps=reasoning_steps,
                final_result=final_result,
                overall_confidence=overall_confidence,
                raw_response=response
            )

        except Exception as e:
            logger.error(f"Error procesando respuesta CoT: {e}")
            raise

    def extract_reasoning_steps(self, response: str) -> List[ReasoningStep]:
        """Extrae pasos de razonamiento"""

        steps = []

        # Patrones para identificar pasos
        step_pattern = r'PASO (\d+):\s*([^\n]+)'
        reasoning_pattern = r'Razonamiento:\s*([^\n]+(?:\n(?!PASO|Resultado:)[^\n]+)*)'
        result_pattern = r'Resultado:\s*([^\n]+)'

        # Encontrar todos los pasos
        step_matches = re.finditer(step_pattern, response, re.IGNORECASE)

        for step_match in step_matches:
            step_num = int(step_match.group(1))
            step_title = step_match.group(2).strip()

            # Buscar razonamiento y resultado para este paso
            step_start = step_match.end()
            next_step = re.search(r'PASO \d+:', response[step_start:], re.IGNORECASE)
            step_end = step_start + next_step.start() if next_step else len(response)

            step_content = response[step_start:step_end]

            # Extraer razonamiento
            reasoning_match = re.search(reasoning_pattern, step_content, re.IGNORECASE | re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

            # Extraer resultado
            result_match = re.search(result_pattern, step_content, re.IGNORECASE)
            result = result_match.group(1).strip() if result_match else ""

            # Calcular confianza del paso
            confidence = self.calculate_step_confidence(reasoning, result)

            steps.append(ReasoningStep(
                step_number=step_num,
                title=step_title,
                reasoning=reasoning,
                result=result,
                confidence=confidence
            ))

        return steps

    def extract_final_json(self, response: str) -> Dict:
        """Extrae JSON final de la respuesta"""

        # Buscar JSON después de "RESULTADO FINAL JSON:"
        json_start = response.find("RESULTADO FINAL JSON:")
        if json_start != -1:
            json_content = response[json_start:]

            # Buscar el JSON
            brace_start = json_content.find('{')
            if brace_start != -1:
                json_content = json_content[brace_start:]

                # Encontrar el final del JSON
                brace_count = 0
                json_end = 0

                for i, char in enumerate(json_content):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                if json_end > 0:
                    json_str = json_content[:json_end]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass

        # Fallback: buscar cualquier JSON en la respuesta
        json_match = re.search(r'\{[^}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        raise ValueError("No se pudo extraer JSON válido de la respuesta")

    def calculate_step_confidence(self, reasoning: str, result: str) -> float:
        """Calcula confianza de un paso individual"""

        confidence = 0.5  # Base

        # Aumentar confianza si hay razonamiento detallado
        if reasoning and len(reasoning) > 20:
            confidence += 0.2

        # Aumentar confianza si hay resultado concreto
        if result and len(result) > 0:
            confidence += 0.2

        # Aumentar confianza si menciona conceptos técnicos
        technical_terms = ['framework', 'comando', 'kebab-case', 'repositorio', 'api', 'web']
        if any(term in reasoning.lower() for term in technical_terms):
            confidence += 0.1

        return min(confidence, 1.0)

    def calculate_overall_confidence(self, reasoning_steps: List[ReasoningStep]) -> float:
        """Calcula confianza general del razonamiento"""

        if not reasoning_steps:
            return 0.0

        # Promedio de confianza de pasos
        avg_confidence = sum(step.confidence for step in reasoning_steps) / len(reasoning_steps)

        # Penalizar si faltan pasos
        expected_steps = len(self.reasoning_steps)
        completeness_factor = len(reasoning_steps) / expected_steps

        return avg_confidence * completeness_factor

    def validate_reasoning_quality(self, cot_response: CoTResponse) -> Dict:
        """Valida calidad del razonamiento"""

        quality_metrics = {
            "completeness": len(cot_response.reasoning_steps) / len(self.reasoning_steps),
            "avg_step_confidence": cot_response.overall_confidence,
            "logical_consistency": self.check_logical_consistency(cot_response.reasoning_steps),
            "technical_accuracy": self.check_technical_accuracy(cot_response.reasoning_steps),
            "result_validity": self.check_result_validity(cot_response.final_result)
        }

        # Score general
        overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
        quality_metrics["overall_quality"] = overall_quality

        return quality_metrics

    def check_logical_consistency(self, steps: List[ReasoningStep]) -> float:
        """Verifica consistencia lógica entre pasos"""

        consistency_score = 1.0

        # Verificar que los resultados sean consistentes
        framework_mentioned = None
        privacy_mentioned = None

        for step in steps:
            if "framework" in step.title.lower():
                framework_mentioned = step.result.lower()
            elif "visibilidad" in step.title.lower():
                privacy_mentioned = step.result.lower()

        # Verificar consistencia entre pasos
        if framework_mentioned and privacy_mentioned:
            # Lógica básica: proyectos personales tienden a ser privados
            if "personal" in framework_mentioned and "false" in privacy_mentioned:
                consistency_score -= 0.1

        return consistency_score

    def check_technical_accuracy(self, steps: List[ReasoningStep]) -> float:
        """Verifica precisión técnica"""

        accuracy_score = 1.0

        valid_frameworks = ['react', 'vue', 'angular', 'django', 'fastapi', 'flask', 'rails', 'flutter']

        for step in steps:
            if "framework" in step.title.lower():
                if not any(fw in step.result.lower() for fw in valid_frameworks):
                    accuracy_score -= 0.3
            elif "comando" in step.title.lower():
                # Verificar comandos válidos
                valid_commands = ['npx', 'npm', 'django-admin', 'fastapi-cli', 'rails', 'flutter create']
                if not any(cmd in step.result.lower() for cmd in valid_commands):
                    accuracy_score -= 0.2

        return max(accuracy_score, 0.0)

    def check_result_validity(self, result: Dict) -> float:
        """Verifica validez del resultado final"""

        validity_score = 1.0

        required_fields = ['repo_name', 'framework', 'is_private', 'description', 'init_command']

        for field in required_fields:
            if field not in result:
                validity_score -= 0.2
            elif not result[field]:
                validity_score -= 0.1

        # Verificar formato del repo_name
        if 'repo_name' in result:
            repo_name = result['repo_name']
            if ' ' in repo_name or repo_name != repo_name.lower():
                validity_score -= 0.1

        return max(validity_score, 0.0)