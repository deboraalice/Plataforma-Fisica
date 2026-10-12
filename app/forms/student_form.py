from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from app.services.StudentService import StudentService


class StudentForm(FlaskForm):
    name = StringField(
        "Nome completo",
        validators=[
            DataRequired(message="Informe seu nome."),
            Length(min=3, max=128, message="Nome deve ter entre 3 e 128 caracteres."),
        ],
    )
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="E-mail inválido."),
        ],
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Informe uma senha."),
            Length(min=8, message="A senha deve ter pelo menos 8 caracteres."),
        ],
    )
    confirmar_password = PasswordField(
        "Confirmar senha",
        validators=[
            DataRequired(message="Confirme sua senha."),
            EqualTo("password", message="As senhas não coincidem."),
        ],
    )
    submit = SubmitField("Cadastrar")

    def validate_email(self, field):
        if StudentService.buscar_por_email(field.data):
            raise ValidationError("Já existe uma conta cadastrada com esse e-mail.")    