from app import db
from app.timeutils import agora_utc


class PointTransaction(db.Model):
    """
    Histórico de pontos do aluno (um lançamento por vez que ele ganha pontos).
    O total é a soma dos lançamentos. Assim o Ranking e o Dashboard usam a
    mesma fonte, e dá para saber de onde veio cada ponto.
    """

    __tablename__ = "point_transaction"
    # um mesmo evento (ex.: uma sessão de pomodoro) nunca pontua duas vezes
    __table_args__ = (
        db.UniqueConstraint("reason", "ref_id", name="uq_point_reason_ref"),
    )

    # motivos (novos motivos entram aqui: simulado, login semanal...)
    POMODORO = "pomodoro"

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(30), nullable=False)
    ref_id = db.Column(db.Integer, nullable=True)  # id do evento que gerou os pontos
    created_at = db.Column(db.DateTime, nullable=False, default=agora_utc)

    student_id = db.Column(
        db.Integer, db.ForeignKey("student.id"), nullable=False, index=True
    )
    student = db.relationship(
        "Student",
        backref=db.backref("point_transactions", lazy="dynamic", cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<PointTransaction {self.student_id} {self.amount:+d} {self.reason}>"
