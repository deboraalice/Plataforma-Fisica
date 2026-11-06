from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange


class ActionForm(FlaskForm):
    """Formulário sem campos para proteger ações POST com CSRF."""


class PhysicsTopicContentForm(FlaskForm):
    summary = StringField(
        "Resumo do tópico",
        validators=[DataRequired(message="Informe um resumo."), Length(max=500)],
    )
    content = TextAreaField(
        "Conteúdo teórico",
        validators=[DataRequired(message="Informe o conteúdo teórico.")],
    )
    solved_example = TextAreaField("Exemplo resolvido")
    submit = SubmitField("Salvar conteúdo")


class PhysicsResourceForm(FlaskForm):
    title = StringField(
        "Título do material",
        validators=[DataRequired(message="Informe o título."), Length(max=160)],
    )
    description = TextAreaField("Descrição (opcional)", validators=[Length(max=1000)])
    url = StringField(
        "Link da videoaula ou material",
        validators=[DataRequired(message="Informe um link."), Length(max=1024)],
    )
    submit = SubmitField("Salvar material")


class QuizForm(FlaskForm):
    title = StringField(
        "Nome do simulado",
        validators=[DataRequired(message="Informe o nome."), Length(max=160)],
    )
    points_per_correct = IntegerField(
        "Pontos por questão correta",
        default=1,
        validators=[InputRequired(), NumberRange(min=0, max=100)],
    )
    is_active = BooleanField("Disponível para os alunos", default=True)
    submit = SubmitField("Salvar simulado")


class QuizQuestionForm(FlaskForm):
    prompt = TextAreaField(
        "Enunciado da questão",
        validators=[DataRequired(message="Escreva a questão."), Length(max=2000)],
    )
    option_a = StringField("Alternativa A", validators=[DataRequired(message="Preencha a alternativa A."), Length(max=500)])
    option_b = StringField("Alternativa B", validators=[DataRequired(message="Preencha a alternativa B."), Length(max=500)])
    option_c = StringField("Alternativa C", validators=[DataRequired(message="Preencha a alternativa C."), Length(max=500)])
    option_d = StringField("Alternativa D", validators=[DataRequired(message="Preencha a alternativa D."), Length(max=500)])
    correct_option = SelectField(
        "Alternativa correta",
        choices=[("0", "Selecione"), ("1", "A"), ("2", "B"), ("3", "C"), ("4", "D")],
        validators=[DataRequired(message="Marque a alternativa correta.")],
    )
    explanation = TextAreaField("Comentário da resposta (opcional)")
    submit = SubmitField("Salvar questão")
