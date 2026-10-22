from datetime import datetime

from app import db
from app.models.task import Task

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
        db.session.commit()
        return task

    @staticmethod
    def atualizar(task, formulario):
        TaskService._preencher(task, formulario)
        db.session.commit()
        return task

    @staticmethod
    def alternar_conclusao(task):
        if task.is_done:
            task.status = "pendente"
            task.completed_at = None
        else:
            task.status = "concluida"
            task.completed_at = datetime.utcnow()
        db.session.commit()
        return task

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
