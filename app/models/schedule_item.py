from datetime import datetime, time

from app import db


class ScheduleItem(db.Model):
    """Bloco de estudo no cronograma semanal de um aluno."""

    __tablename__ = "schedule_item"

    DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    # código salvo no banco -> nome da cor (as cores ficam no CSS: .c-indigo etc.)
    CORES = {
        "indigo": "Índigo",
        "cyan": "Ciano",
        "green": "Verde",
        "violet": "Violeta",
        "amber": "Âmbar",
        "red": "Vermelho",
    }

    # a grade da tela vai das 06:00 às 22:00, com 48 px por hora
    GRADE_INICIO = time(6, 0)
    GRADE_FIM = time(22, 0)
    DURACAO_MINIMA = 30  # minutos
    ALTURA_HORA = 48  # px

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(80), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0 = segunda ... 6 = domingo
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    color = db.Column(db.String(10), nullable=False, default="indigo")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student_id = db.Column(
        db.Integer, db.ForeignKey("student.id"), nullable=False, index=True
    )
    student = db.relationship(
        "Student",
        backref=db.backref("schedule_items", lazy="dynamic", cascade="all, delete-orphan"),
    )

    @staticmethod
    def minutos(hora):
        return hora.hour * 60 + hora.minute

    @property
    def day_name(self):
        return self.DIAS[self.weekday]

    @property
    def start_label(self):
        return self.start_time.strftime("%H:%M")

    @property
    def end_label(self):
        return self.end_time.strftime("%H:%M")

    @property
    def top_px(self):
        """Distância do topo da coluna, pelos minutos reais (e não só horas cheias)."""
        desde_o_inicio = self.minutos(self.start_time) - self.minutos(self.GRADE_INICIO)
        return round(desde_o_inicio * self.ALTURA_HORA / 60 + 2)

    @property
    def height_px(self):
        duracao = self.minutos(self.end_time) - self.minutos(self.start_time)
        return round(duracao * self.ALTURA_HORA / 60 - 4)

    def to_dict(self):
        return {
            "id": self.id,
            "subject": self.subject,
            "weekday": self.weekday,
            "start_time": self.start_label,
            "end_time": self.end_label,
            "color": self.color,
        }

    def __repr__(self):
        return f"<ScheduleItem {self.id} {self.subject!r} {self.day_name}>"
