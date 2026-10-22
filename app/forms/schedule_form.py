from datetime import time

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import AnyOf, DataRequired, Length, ValidationError

from app.models.schedule_item import ScheduleItem


def _limpar(valor):
    return valor.strip() if isinstance(valor, str) else valor


def _ler_hora(texto):
    """Converte 'HH:MM' em time; devolve None se não for uma hora válida."""
    try:
        hora = time.fromisoformat(str(texto))
    except ValueError:
        return None
    return hora if hora.tzinfo is None else None


class ScheduleForm(FlaskForm):
    """
    Valida os dados enviados em JSON pela tela de Cronograma.
    O CSRF é verificado pelo CSRFProtect global (cabeçalho X-CSRFToken).

    A regra de conflito de horários (que precisa consultar o banco) fica no
    ScheduleService e é aplicada pela rota depois desta validação.
    """

    class Meta:
        csrf = False

    subject = StringField(
        "Disciplina",
        filters=[_limpar],
        validators=[
            DataRequired(message="Informe a disciplina."),
            Length(max=80, message="A disciplina deve ter no máximo 80 caracteres."),
        ],
    )
    weekday = StringField("Dia da semana", validators=[DataRequired(message="Informe o dia da semana.")])
    start_time = StringField("Início", filters=[_limpar], validators=[DataRequired(message="Informe o início.")])
    end_time = StringField("Fim", filters=[_limpar], validators=[DataRequired(message="Informe o fim.")])
    color = StringField(
        "Cor",
        default="indigo",
        validators=[AnyOf(list(ScheduleItem.CORES), message="Cor inválida.")],
    )

    def validate_weekday(self, field):
        try:
            dia = int(str(field.data))
        except ValueError:
            raise ValidationError("Dia da semana inválido.")
        if not 0 <= dia <= 6:
            raise ValidationError("Dia da semana inválido.")
        self.dia = dia

    def validate_start_time(self, field):
        self.inicio = _ler_hora(field.data)
        if self.inicio is None:
            raise ValidationError("Horário inválido.")
        if self.inicio < ScheduleItem.GRADE_INICIO:
            raise ValidationError("O cronograma começa às 06:00.")

    def validate_end_time(self, field):
        self.fim = _ler_hora(field.data)
        if self.fim is None:
            raise ValidationError("Horário inválido.")
        if self.fim > ScheduleItem.GRADE_FIM:
            raise ValidationError("O cronograma termina às 22:00.")

        # só compara se o início também for válido
        inicio = getattr(self, "inicio", None)
        if inicio is None:
            return
        if self.fim <= inicio:
            raise ValidationError("O horário de fim deve ser após o início.")
        duracao = ScheduleItem.minutos(self.fim) - ScheduleItem.minutos(inicio)
        if duracao < ScheduleItem.DURACAO_MINIMA:
            raise ValidationError(
                f"O bloco deve ter pelo menos {ScheduleItem.DURACAO_MINIMA} minutos."
            )
