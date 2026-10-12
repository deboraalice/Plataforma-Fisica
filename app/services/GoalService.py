from datetime import datetime

from app import db
from app.models.goal import Goal


class GoalService:
    """Toda consulta filtra por student_id: cada aluno só vê as próprias metas."""

    @staticmethod
    def listar(student_id):
        # em andamento primeiro (prazo mais próximo antes); concluídas no fim
        return (
            Goal.query.filter_by(student_id=student_id)
            .order_by(Goal.status == "concluida", Goal.due_date, Goal.id)
            .all()
        )

    @staticmethod
    def buscar(goal_id, student_id):
        return Goal.query.filter_by(id=goal_id, student_id=student_id).first()

    @staticmethod
    def contar(student_id):
        metas = Goal.query.filter_by(student_id=student_id).all()
        concluidas = sum(1 for m in metas if m.is_done)
        return {
            "todas": len(metas),
            "abertas": len(metas) - concluidas,
            "concluidas": concluidas,
        }

    @staticmethod
    def criar(student_id, formulario):
        goal = Goal(student_id=student_id)
        GoalService._preencher(goal, formulario)
        db.session.add(goal)
        db.session.commit()
        return goal

    @staticmethod
    def atualizar(goal, formulario):
        GoalService._preencher(goal, formulario)
        db.session.commit()
        return goal

    @staticmethod
    def concluir(goal):
        # concluir é definitivo (como no protótipo); repetir não muda nada
        if not goal.is_done:
            goal.status = "concluida"
            goal.completed_at = datetime.utcnow()
            db.session.commit()
        return goal

    @staticmethod
    def remover(goal):
        db.session.delete(goal)
        db.session.commit()

    @staticmethod
    def _preencher(goal, formulario):
        goal.title = formulario.title.data
        goal.type = formulario.type.data
        goal.due_date = formulario.prazo
