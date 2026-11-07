from datetime import datetime

from app import db
from app.models.point_transaction import PointTransaction
from app.models.task import Task
from app.services.PointsService import PointsService

class TaskService:
    """
    Toda consulta filtra por student_id: um aluno nunca enxerga nem altera
    as tarefas de outro, mesmo que adivinhe o id na URL.
    """

    @staticmethod
    def listar(student_id):
        # abertas primeiro (prazo mais próximo antes); concluídas no fim
        return (
            Task.query.filter_by(student_id=student_id)
            .order_by(Task.status == "concluida", Task.due_date, Task.id)
            .all()
        )

    @staticmethod
    def buscar(task_id, student_id):
        return Task.query.filter_by(id=task_id, student_id=student_id).first()

    @staticmethod
    def contar(student_id):
        tarefas = Task.query.filter_by(student_id=student_id).all()
        contagem = {"todas": len(tarefas), "pendente": 0, "em_andamento": 0, "concluida": 0}
        for t in tarefas:
            contagem[t.status] += 1
        contagem["abertas"] = contagem["pendente"] + contagem["em_andamento"]
        return contagem

    @staticmethod
    def criar(student_id, formulario):
        task = Task(student_id=student_id)
        TaskService._preencher(task, formulario)
        db.session.add(task)
        db.session.flush()
        if task.is_done:
            TaskService._pontuar_conclusao(task)
        db.session.commit()
        return task

    @staticmethod
    def atualizar(task, formulario):
        estava_concluida = task.is_done
        TaskService._preencher(task, formulario)
        if task.is_done and not estava_concluida:
            TaskService._pontuar_conclusao(task)
        db.session.commit()
        return task

    @staticmethod
    def alternar_conclusao(task):
        points_awarded = 0
        if task.is_done:
            task.status = "pendente"
            task.completed_at = None
        else:
            task.status = "concluida"
            task.completed_at = datetime.utcnow()
            points_awarded = 20 if TaskService._pontuar_conclusao(task) else 0
        db.session.commit()
        return task, points_awarded

    @staticmethod
    def _pontuar_conclusao(task):
        ja_pontuada = PointTransaction.query.filter_by(
            reason=PointTransaction.TASK_COMPLETE,
            ref_id=task.id,
        ).first()
        if ja_pontuada is None:
            PointsService.conceder(
                task.student_id, 20, PointTransaction.TASK_COMPLETE, task.id
            )
            return True
        return False

    @staticmethod
    def remover(task):
        db.session.delete(task)
        db.session.commit()

    @staticmethod
    def _preencher(task, formulario):
        task.title = formulario.title.data
        task.description = formulario.description.data or ""
        task.subject = formulario.subject.data
        task.due_date = formulario.prazo
        task.priority = formulario.priority.data

        novo_status = formulario.status.data
        if novo_status == "concluida" and not task.is_done:
            task.completed_at = datetime.utcnow()
        elif novo_status != "concluida":
            task.completed_at = None
        task.status = novo_status
