from datetime import date, datetime

from app import db


class Goal(db.Model):
    """Meta de estudo de um aluno (curto, médio ou longo prazo)."""

    # código salvo no banco -> rótulo exibido na tela
    TIPOS = {"curto": "Curto prazo", "medio": "Médio prazo", "longo": "Longo prazo"}
    STATUS = {"pendente": "Pendente", "concluida": "Concluída"}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(10), nullable=False, default="curto")
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pendente")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    student_id = db.Column(
        db.Integer, db.ForeignKey("student.id"), nullable=False, index=True
    )
    student = db.relationship(
        "Student",
        backref=db.backref("goals", lazy="dynamic", cascade="all, delete-orphan"),
    )

    @property
    def is_done(self):
        return self.status == "concluida"

    @property
    def is_overdue(self):
        return not self.is_done and self.due_date < date.today()

    @property
    def type_label(self):
        return self.TIPOS.get(self.type, self.type)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "due_date": self.due_date.isoformat(),
            "status": self.status,
            "is_overdue": self.is_overdue,
        }

    def __repr__(self):
        return f"<Goal {self.id} {self.title!r}>"
