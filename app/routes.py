from flask import redirect, render_template, request, session, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.forms.login_form import LoginForm
from app.forms.student_form import StudentForm
from app.services.StudentService import StudentService
from app.services.ProfessorService import ProfessorService
from app.services.AuthService import AuthService, SuapAuthError

@app.route("/")
def index():
    return render_template("index.html")
 
 
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
 
    formulario = LoginForm()
 
    if formulario.validate_on_submit():
        email = formulario.email.data
 
        usuario = StudentService.buscar_por_email(email) or \
            ProfessorService.buscar_por_email(email)
 
        if usuario is None or not usuario.check_password(formulario.password.data):
            flash("E-mail ou senha inválidos.", "danger")
            return render_template("auth/login.html", formulario=formulario)
 
        login_user(usuario)
        flash(f"Bem-vindo(a), {usuario.name}!", "success")
        return redirect(url_for("index"))
 
    return render_template("auth/login.html", formulario=formulario)
 
 
@app.route("/login/suap")
def login_suap():
    try:
        authorization_url, state = AuthService.get_authorization_url()
    except RuntimeError:
        flash(
            "O login com o SUAP está temporariamente indisponível. "
            "Use o cadastro tradicional.",
            "warning",
        )
        return redirect(url_for("login"))
 
    session["suap_oauth_state"] = state
    return redirect(authorization_url)
 
 
@app.route("/login/suap/callback")
def login_suap_callback():
    state = session.pop("suap_oauth_state", None)
 
    if state is None or state != request.args.get("state"):
        flash("Sessão de login com o SUAP inválida ou expirada. Tente novamente.", "danger")
        return redirect(url_for("login"))
 
    if request.args.get("error"):
        flash("Login com o SUAP cancelado.", "warning")
        return redirect(url_for("login"))
 
    try:
        dados_suap = AuthService.get_user_data(request.url, state=state)
    except SuapAuthError as e:
        flash(str(e), "danger")
        return redirect(url_for("login"))
 
    if dados_suap["tipo_vinculo"] == "Aluno":
        usuario = StudentService.criar_ou_atualizar_via_suap(dados_suap)
    elif dados_suap["tipo_vinculo"] == "Servidor":
        usuario = ProfessorService.criar_ou_atualizar_via_suap(dados_suap)
    else:
        flash(
            f"Vínculo '{dados_suap['tipo_vinculo']}' não é suportado pela plataforma.",
            "danger",
        )
        return redirect(url_for("login"))
 
    login_user(usuario)
    flash(f"Bem-vindo(a), {usuario.name}!", "success")
    return redirect(url_for("index"))
 
 
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você saiu da plataforma.", "info")
    return redirect(url_for("index"))
 
 
@app.route("/student/cadastrar", methods=["GET", "POST"])
def cadastrar_student():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
 
    formulario = StudentForm()
 
    if formulario.validate_on_submit():
        student = StudentService.salvar(formulario)
        login_user(student)
        flash(f"Cadastro concluído! Bem-vindo(a), {student.name}.", "success")
        return redirect(url_for("index"))
 
    return render_template("student/signin.html", formulario=formulario)