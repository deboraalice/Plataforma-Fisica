from datetime import date, datetime

from app import db


class Task(db.Model):
    """Tarefa de estudo de um aluno."""

    # código salvo no banco -> rótulo exibido na tela
    PRIORIDADES = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
    STATUS = {
        "pendente": "Pendente",
        "em_andamento": "Em andamento",
        "concluida": "Concluída",
    }

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False, default="")
    subject = db.Column(db.String(60), nullable=False, default="Física")
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="media")
    status = db.Column(db.String(20), nullable=False, default="pendente")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    student_id = db.Column(
        db.Integer, db.ForeignKey("student.id"), nullable=False, index=True
    )
    student = db.relationship(
        "Student",
        backref=db.backref("tasks", lazy="dynamic", cascade="all, delete-orphan"),
    )

    @property
    def is_done(self):
        return self.status == "concluida"

    @property
    def is_overdue(self):
        return not self.is_done and self.due_date < date.today()

    @property
    def priority_label(self):
        return self.PRIORIDADES.get(self.priority, self.priority)

    @property
    def status_label(self):
        return self.STATUS.get(self.status, self.status)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "due_date": self.due_date.isoformat(),
            "priority": self.priority,
            "status": self.status,
            "is_overdue": self.is_overdue,
        }

    def __repr__(self):
        return f"<Task {self.id} {self.title!r}>"
