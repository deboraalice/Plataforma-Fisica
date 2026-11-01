from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

from app.services.StudentService import StudentService
from app.services.ProfessorService import ProfessorService


class RegistrationForm(FlaskForm):
    profile_type = SelectField(
        "Tipo de perfil",
        choices=[
            ("", "Selecione seu perfil"),
            ("student", "Aluno"),
            ("professor", "Professor"),
        ],
        validators=[DataRequired(message="Escolha o tipo de perfil.")],
    )
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
            Length(min=6, message="A senha deve ter pelo menos 6 caracteres."),
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
        field.data = field.data.strip().lower()
        if (
            StudentService.buscar_por_email(field.data)
            or ProfessorService.buscar_por_email(field.data)
        ):
            raise ValidationError("Já existe uma conta cadastrada com esse e-mail.")
