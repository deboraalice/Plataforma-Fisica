from sqlalchemy import func

from app import db
from app.models.point_transaction import PointTransaction
from app.models.goal import Goal
from app.models.physics import FirstQuizCompletion, QuizAttempt, TopicCompletion
from app.models.student import Student
from app.models.task import Task
from app.services.PointsService import PointsService


class RankingService:
    """Classificação global dos alunos pelo total do histórico de pontos."""

    @staticmethod
    def registrar_pontos_historicos():
        """Concede os novos bônus a atividades já concluídas, sem duplicá-los."""
        for task in Task.query.filter_by(status="concluida").all():
            if not PointTransaction.query.filter_by(
                reason=PointTransaction.TASK_COMPLETE, ref_id=task.id
            ).first():
                PointsService.conceder(
                    task.student_id, 20, PointTransaction.TASK_COMPLETE, task.id
                )

        for goal in Goal.query.filter_by(status="concluida").all():
            if not PointTransaction.query.filter_by(
                reason=PointTransaction.GOAL_COMPLETE, ref_id=goal.id
            ).first():
                PointsService.conceder(
                    goal.student_id, 100, PointTransaction.GOAL_COMPLETE, goal.id
                )

        for completion in TopicCompletion.query.all():
            if not PointTransaction.query.filter_by(
                reason=PointTransaction.TOPIC_COMPLETE, ref_id=completion.id
            ).first():
                PointsService.conceder(
                    completion.student_id,
                    30,
                    PointTransaction.TOPIC_COMPLETE,
                    completion.id,
                )

        tentativas_com_bom_desempenho = QuizAttempt.query.filter(
            QuizAttempt.completed_at.isnot(None), QuizAttempt.question_count > 0
        ).all()
        quizzes_qualificados = {}
        for tentativa in tentativas_com_bom_desempenho:
            if tentativa.correct_count / tentativa.question_count >= 0.75:
                quizzes_qualificados.setdefault(
                    (tentativa.student_id, tentativa.quiz_id), tentativa
                )

        for (student_id, quiz_id), tentativa in quizzes_qualificados.items():
            if FirstQuizCompletion.query.filter_by(
                student_id=student_id, quiz_id=quiz_id
            ).first():
                continue
            bonus = FirstQuizCompletion(
                student_id=student_id,
                quiz_id=quiz_id,
                attempt_id=tentativa.id,
                points_awarded=150,
            )
            db.session.add(bonus)
            db.session.flush()
            PointsService.conceder(
                student_id, 150, PointTransaction.QUIZ_MASTERY, bonus.id
            )

        db.session.commit()

    @staticmethod
    def classificacao():
        total = func.coalesce(func.sum(PointTransaction.amount), 0)
        registros = (
            db.session.query(Student.id, Student.name, total.label("points"))
            .outerjoin(PointTransaction, PointTransaction.student_id == Student.id)
            .group_by(Student.id, Student.name)
            .order_by(total.desc(), Student.name.asc(), Student.id.asc())
            .all()
        )
        return [
            {"student_id": row.id, "name": row.name, "points": int(row.points), "position": index}
            for index, row in enumerate(registros, start=1)
        ]

    @staticmethod
    def dados_da_pagina(student_id):
        classificacao = RankingService.classificacao()
        propria = next(
            (aluno for aluno in classificacao if aluno["student_id"] == student_id),
            None,
        )
        return {
            "classificacao": classificacao,
            "podio": [aluno for aluno in classificacao if aluno["position"] <= 3],
            "propria": propria,
            "alunos_count": len(classificacao),
        }
