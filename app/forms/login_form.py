from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe seu e-mail."),
            Email(message="E-mail inválido."),
        ],
    )
    password = PasswordField(
        "Senha", validators=[DataRequired(message="Informe sua senha.")]
    )
    submit = SubmitField("Entrar")