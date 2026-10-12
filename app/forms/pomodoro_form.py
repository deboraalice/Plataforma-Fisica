from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, ValidationError

from app.models.pomodoro_session import PomodoroSession


class PomodoroForm(FlaskForm):
    """Valida o pedido para iniciar uma sessão de foco (CSRF pelo CSRFProtect global)."""

    class Meta:
        csrf = False

    minutes = StringField("Duração", validators=[DataRequired(message="Informe a duração.")])

    def validate_minutes(self, field):
        try:
            minutos = int(str(field.data))
        except ValueError:
            raise ValidationError("Duração inválida.")
        if not PomodoroSession.MIN_MINUTOS <= minutos <= PomodoroSession.MAX_MINUTOS:
            raise ValidationError(
                f"A duração deve ficar entre {PomodoroSession.MIN_MINUTOS} "
                f"e {PomodoroSession.MAX_MINUTOS} minutos."
            )
        self.minutos = minutos
