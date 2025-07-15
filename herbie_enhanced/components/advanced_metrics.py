import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os

from ..core_system import (
    ProjectAnalyzer, ProjectExecutor, LearningEngine, MetricsCollector,
    ProjectRequest, ProjectAnalysis, ExecutionResult, UserFeedback
)


class AdvancedMetricsCollector(MetricsCollector):
    """
    Recolector avanzado de métricas con análisis en tiempo real
    """

    def __init__(self, db_path: str = "herbie_metrics.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Inicializa base de datos de métricas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS metrics
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           session_id
                           TEXT,
                           framework
                           TEXT,
                           complexity_score
                           INTEGER,
                           predicted_success
                           REAL,
                           actual_success
                           BOOLEAN,
                           user_satisfaction
                           REAL,
                           setup_time
                           REAL,
                           confidence
                           REAL,
                           feedback_received
                           BOOLEAN,
                           timestamp
                           DATETIME
                       )
                       ''')

        conn.commit()
        conn.close()

    def collect_metrics(self, analysis: ProjectAnalysis,
                        result: ExecutionResult,
                        feedback: Optional[UserFeedback] = None) -> None:
        """Recolecta y almacena métricas"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
                       INSERT INTO metrics
                       (session_id, framework, complexity_score, predicted_success,
                        actual_success, user_satisfaction, setup_time, confidence,
                        feedback_received, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                       ''', (
                           getattr(analysis, 'session_id', 'unknown'),
                           analysis.framework,
                           analysis.complexity_score,
                           analysis.predicted_success,
                           result.success,
                           feedback.satisfaction if feedback else None,
                           result.execution_time,
                           analysis.confidence,
                           feedback is not None,
                           datetime.now()
                       ))

        conn.commit()
        conn.close()

    def get_performance_summary(self, days: int = 7) -> Dict:
        """Obtiene resumen de rendimiento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Métricas de los últimos días
        cursor.execute('''
            SELECT 
                COUNT(*) as total_projects,
                AVG(CAST(actual_success AS REAL)) as success_rate,
                AVG(user_satisfaction) as avg_satisfaction,
                AVG(setup_time) as avg_setup_time,
                AVG(confidence) as avg_confidence
            FROM metrics 
            WHERE timestamp >= datetime('now', '-{} days')
        '''.format(days))

        row = cursor.fetchone()

        # Distribución por framework
        cursor.execute('''
            SELECT framework, COUNT(*), AVG(CAST(actual_success AS REAL))
            FROM metrics 
            WHERE timestamp >= datetime('now', '-{} days')
            GROUP BY framework
        '''.format(days))

        framework_stats = cursor.fetchall()

        conn.close()

        return {
            'total_projects': row[0] or 0,
            'success_rate': row[1] or 0,
            'avg_satisfaction': row[2] or 0,
            'avg_setup_time': row[3] or 0,
            'avg_confidence': row[4] or 0,
            'framework_stats': [
                {'framework': f[0], 'count': f[1], 'success_rate': f[2] or 0}
                for f in framework_stats
            ]
        }
