from app import db
from app.timeutils import agora_utc

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(128), nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=False)
    access_code = db.Column(db.String(6), unique=True, nullable=True, index=True)
    access_code_active = db.Column(db.Boolean, nullable=False, default=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    students = db.relationship('Student', backref='team', lazy='dynamic')


class TeamMembership(db.Model):
    """Histórico de períodos em que um aluno pertenceu a uma turma."""

    __tablename__ = "team_membership"
    __table_args__ = (
        db.Index("ix_team_membership_student_team", "student_id", "team_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("team.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    # NULL indica vínculos anteriores ao início do histórico na aplicação.
    joined_at = db.Column(db.DateTime, nullable=True, default=agora_utc)
    left_at = db.Column(db.DateTime, nullable=True)

    team = db.relationship("Team", backref=db.backref("memberships", lazy="dynamic"))
    student = db.relationship("Student", backref=db.backref("team_memberships", lazy="dynamic"))
