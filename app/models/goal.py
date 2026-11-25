from datetime import date, datetime

from app import db
from app.timeutils import agora_utc


class Goal(db.Model):
    """Meta de estudo antiga (criada pelo aluno). Mantida só para não quebrar
    o banco; pode ser removida depois com uma migração."""

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


class GoalClaim(db.Model):
    """Degrau de uma meta global já resgatado por um aluno."""

    __tablename__ = "goal_claim"
    __table_args__ = (
        db.UniqueConstraint("student_id", "goal_key", "tier", name="uq_goal_claim"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    goal_key = db.Column(db.String(40), nullable=False)
    tier = db.Column(db.Integer, nullable=False)  # índice do degrau (0, 1, 2...)
    points_awarded = db.Column(db.Integer, nullable=False, default=0)
    claimed_at = db.Column(db.DateTime, nullable=False, default=agora_utc)

    student = db.relationship(
        "Student",
        backref=db.backref("goal_claims", lazy="dynamic", cascade="all, delete-orphan"),
    )


class StudentActivityDay(db.Model):
    """Um registro por dia em que o aluno acessou a plataforma."""

    __tablename__ = "student_activity_day"
    __table_args__ = (
        db.UniqueConstraint("student_id", "day", name="uq_activity_student_day"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    day = db.Column(db.Date, nullable=False)

    student = db.relationship(
        "Student",
        backref=db.backref("activity_days", lazy="dynamic", cascade="all, delete-orphan"),
    )