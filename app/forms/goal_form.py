from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import AnyOf, DataRequired, Length, ValidationError

from app.models.goal import Goal


def _limpar(valor):
    return valor.strip() if isinstance(valor, str) else valor


class GoalForm(FlaskForm):
    """
    Valida os dados enviados em JSON pela tela de Metas.
    O CSRF é verificado pelo CSRFProtect global (cabeçalho X-CSRFToken).
    """

    class Meta:
        csrf = False

    title = StringField(
        "Título",
        filters=[_limpar],
        validators=[
            DataRequired(message="Informe o título."),
            Length(max=120, message="O título deve ter no máximo 120 caracteres."),
        ],
    )
    type = StringField(
        "Tipo",
        validators=[AnyOf(list(Goal.TIPOS), message="Tipo de meta inválido.")],
    )
    due_date = StringField(
        "Prazo",
        filters=[_limpar],
        validators=[DataRequired(message="Informe o prazo.")],
    )

    def validate_due_date(self, field):
        try:
            self.prazo = date.fromisoformat(field.data)
        except (TypeError, ValueError):
            raise ValidationError("Data inválida.")
