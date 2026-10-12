from app import db
from app.timeutils import agora_utc, descrever_quando


class PomodoroSession(db.Model):
    """
    Sessão de FOCO do Pomodoro. (O descanso é só um cronômetro na tela e não
    é guardado.) A sessão é aberta quando o aluno aperta "Iniciar" e só rende
    pontos se o servidor confirmar que o tempo realmente passou.
    """

    __tablename__ = "pomodoro_session"

    STATUS = ("em_andamento", "concluida", "cancelada")

    MIN_MINUTOS = 5
    MAX_MINUTOS = 60
    PONTOS_POR_MINUTO = 2  # 25 min = 50 pontos, como no protótipo
    TOLERANCIA_SEGUNDOS = 5  # folga para o atraso da rede

    id = db.Column(db.Integer, primary_key=True)
    minutes = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="em_andamento")
    started_at = db.Column(db.DateTime, nullable=False, default=agora_utc)
    completed_at = db.Column(db.DateTime, nullable=True)
    points_awarded = db.Column(db.Integer, nullable=False, default=0)

    student_id = db.Column(
        db.Integer, db.ForeignKey("student.id"), nullable=False, index=True
    )
    student = db.relationship(
        "Student",
        backref=db.backref("pomodoro_sessions", lazy="dynamic", cascade="all, delete-orphan"),
    )

    @classmethod
    def pontos_para(cls, minutos):
        return minutos * cls.PONTOS_POR_MINUTO

    def tempo_completo(self, agora):
        """O tempo da sessão já passou? (pausas só deixam o tempo real maior)"""
        decorrido = (agora - self.started_at).total_seconds()
        return decorrido >= self.minutes * 60 - self.TOLERANCIA_SEGUNDOS

    @property
    def when_label(self):
        return descrever_quando(self.completed_at)

    def to_dict(self):
        return {"id": self.id, "minutes": self.minutes, "status": self.status}

    def __repr__(self):
        return f"<PomodoroSession {self.id} {self.minutes}min {self.status}>"
