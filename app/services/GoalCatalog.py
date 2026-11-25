from dataclasses import dataclass
from typing import Callable

from sqlalchemy import func

from app import db
from app.models.goal import StudentActivityDay
from app.models.physics import (
    FirstQuestionScore,
    FirstQuizCompletion,
    PhysicsUnit,
    QuizAnswer,
    QuizAttempt,
    TopicCompletion,
)
from app.models.pomodoro_session import PomodoroSession
from app.models.task import Task


@dataclass(frozen=True)
class MetaDef:
    key: str
    titulo: str
    descricao: str
    icone: str
    unidade: str                      # "pomodoros", "semanas"...
    degraus: tuple                    # ((alvo, pontos), ...) em ordem crescente
    medir: Callable[[int], int]       # student_id -> progresso atual


def _pomodoros(sid):
    return PomodoroSession.query.filter_by(student_id=sid, status="concluida").count()


def _minutos_foco(sid):
    return int(
        db.session.query(func.coalesce(func.sum(PomodoroSession.minutes), 0))
        .filter(PomodoroSession.student_id == sid, PomodoroSession.status == "concluida")
        .scalar()
    )


def _topicos(sid):
    return TopicCompletion.query.filter_by(student_id=sid).count()


def _modulos(sid):
    feitos = {c.topic_id for c in TopicCompletion.query.filter_by(student_id=sid)}
    total = 0
    for unidade in PhysicsUnit.query.all():
        ids = [t.id for t in unidade.topics]
        if ids and all(i in feitos for i in ids):
            total += 1
    return total


def _simulados(sid):
    """Simulados distintos finalizados com pelo menos uma questão respondida."""
    return (
        db.session.query(func.count(func.distinct(QuizAttempt.quiz_id)))
        .filter(
            QuizAttempt.student_id == sid,
            QuizAttempt.completed_at.isnot(None),
            db.exists().where(QuizAnswer.attempt_id == QuizAttempt.id),
        )
        .scalar()
    ) or 0


def _simulados_mestre(sid):
    return FirstQuizCompletion.query.filter_by(student_id=sid).count()


def _acertos_de_primeira(sid):
    return FirstQuestionScore.query.filter(
        FirstQuestionScore.student_id == sid,
        FirstQuestionScore.points_awarded > 0,
    ).count()


def _tarefas(sid):
    return Task.query.filter_by(student_id=sid, status="concluida").count()


def _semanas_de_acesso(sid):
    dias = [d.day for d in StudentActivityDay.query.filter_by(student_id=sid)]
    return len({d.isocalendar()[:2] for d in dias})


CATALOGO = (
    MetaDef("login_semanal", "Presença na plataforma",
            "Acesse a plataforma em semanas diferentes.", "📅", "semanas",
            ((1, 10), (4, 60), (8, 120), (12, 200), (26, 400)), _semanas_de_acesso),
    MetaDef("pomodoros", "Foco total",
            "Conclua sessões de foco no Pomodoro.", "🍅", "pomodoros",
            ((1, 20), (4, 50), (10, 100), (20, 200), (30, 300), (50, 500)), _pomodoros),
    MetaDef("minutos_foco", "Maratonista",
            "Acumule minutos de foco concluídos.", "⏱️", "min de foco",
            ((60, 40), (300, 120), (600, 250), (1500, 600)), _minutos_foco),
    MetaDef("topicos", "Explorador de tópicos",
            "Conclua tópicos de Física.", "📘", "tópicos",
            ((1, 30), (3, 60), (6, 120), (10, 250)), _topicos),
    MetaDef("modulos", "Módulo completo",
            "Conclua todos os tópicos de um módulo.", "🏁", "módulos",
            ((1, 150), (2, 250), (3, 400)), _modulos),
    MetaDef("simulados", "Hora do simulado",
            "Finalize simulados diferentes.", "📝", "simulados",
            ((1, 30), (3, 80), (5, 150), (10, 300), (20, 600)), _simulados),
    MetaDef("simulados_mestre", "Mestre dos simulados",
            "Alcance o bônus de desempenho em simulados.", "🏆", "simulados",
            ((1, 100), (3, 250), (5, 500)), _simulados_mestre),
    MetaDef("acertos", "Mira certeira",
            "Acerte questões de primeira.", "🎯", "acertos",
            ((10, 50), (50, 150), (100, 300), (250, 700)), _acertos_de_primeira),
    MetaDef("tarefas", "Mão na massa",
            "Conclua tarefas de estudo.", "✅", "tarefas",
            ((1, 15), (5, 50), (10, 100), (25, 250)), _tarefas),
)

CATALOGO_POR_CHAVE = {m.key: m for m in CATALOGO}