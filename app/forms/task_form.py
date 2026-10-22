from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import AnyOf, DataRequired, Length, Optional, ValidationError

from app.models.task import Task


def _limpar(valor):
    return valor.strip() if isinstance(valor, str) else valor


class TaskForm(FlaskForm):
    """
    Valida os dados enviados em JSON pela tela de Tarefas.

    O token CSRF é verificado pelo CSRFProtect global (cabeçalho X-CSRFToken),
    por isso a checagem própria do formulário fica desligada.
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
    description = StringField(
        "Descrição",
        filters=[_limpar],
        validators=[
            Optional(),
            Length(max=500, message="A descrição deve ter no máximo 500 caracteres."),
        ],
    )
    subject = StringField(
        "Disciplina",
        default="Física",
        filters=[_limpar],
        validators=[
            DataRequired(message="Informe a disciplina."),
            Length(max=60, message="A disciplina deve ter no máximo 60 caracteres."),
        ],
    )
    due_date = StringField(
        "Prazo",
        filters=[_limpar],
        validators=[DataRequired(message="Informe o prazo.")],
    )
    priority = StringField(
        "Prioridade",
        default="media",
        validators=[
            AnyOf(list(Task.PRIORIDADES), message="Prioridade inválida."),
        ],
    )
    status = StringField(
        "Status",
        default="pendente",
        validators=[AnyOf(list(Task.STATUS), message="Status inválido.")],
    )

    def validate_due_date(self, field):
        try:
            self.prazo = date.fromisoformat(field.data)
        except (TypeError, ValueError):
            raise ValidationError("Data inválida.")
