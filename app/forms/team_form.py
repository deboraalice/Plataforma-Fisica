from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError


class TeamForm(FlaskForm):
    nome = StringField(
        "Nome da turma",
        validators=[
            DataRequired(message="Informe o nome da turma."),
            Length(max=128, message="O nome pode ter até 128 caracteres."),
        ],
    )
    submit = SubmitField("Salvar turma")


class TeamJoinForm(FlaskForm):
    code = StringField(
        "Código da turma",
    )

    def validate_code(self, field):
        field.data = (field.data or "").strip().upper()
        if not field.data:
            raise ValidationError("Informe o código da turma.")
        if len(field.data) != 6:
            raise ValidationError("O código deve ter 6 caracteres.")
        if not field.data.isalnum() or not field.data.isascii():
            raise ValidationError("Use as 6 letras ou números do código.")


class ActionForm(FlaskForm):
    """Formulário sem campos para ações POST protegidas por CSRF."""
