from datetime import date
from flask import jsonify, redirect, render_template, request, session, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.forms.login_form import LoginForm
from app.forms.student_form import StudentForm
from app.forms.task_form import TaskForm
from app.forms.goal_form import GoalForm
from app.forms.schedule_form import ScheduleForm
from app.forms.pomodoro_form import PomodoroForm
from app.decorators import api_student_required, student_required
from app.models.task import Task
from app.models.goal import Goal
from app.models.schedule_item import ScheduleItem
from app.models.student import Student
from app.models.pomodoro_session import PomodoroSession
from app.services.TaskService import TaskService
from app.services.GoalService import GoalService
from app.services.ScheduleService import ScheduleService
from app.services.PointsService import PointsService
from app.services.PomodoroService import PomodoroService, PomodoroError, SessaoJaEncerrada
from app.services.StudentService import StudentService
from app.services.ProfessorService import ProfessorService
from app.services.AuthService import AuthService, SuapAuthError
from app.services.DashboardService import DashboardService

@app.route("/")
def index():
    # visitantes vão direto para o login; quem já entrou vê o painel
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
 
    usuario = current_user._get_current_object()
    # só alunos têm painel de estudos; professores veem uma mensagem simples
    dados = DashboardService.montar(usuario) if isinstance(usuario, Student) else None
    return render_template("index.html", d=dados)
 
 
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


# ---------------------------------------------------------------------------
# Tarefas
#   /tarefas               -> página (HTML renderizado pelo Jinja)
#   /api/tarefas/...       -> rotas JSON chamadas via AJAX (fetch) pela página
# ---------------------------------------------------------------------------

def _resposta_tarefa(task, status=200):
    """JSON com a tarefa, o card já renderizado (Jinja) e os contadores."""
    return jsonify(
        ok=True,
        task=task.to_dict(),
        html=render_template("tasks/_task_card.html", t=task),
        counts=TaskService.contar(current_user.id),
    ), status


def _erros_do_formulario(formulario):
    erros = {campo: msgs[:1] for campo, msgs in formulario.errors.items()}
    return jsonify(ok=False, errors=erros), 400


def _tarefa_ou_404(task_id):
    return TaskService.buscar(task_id, current_user.id)


def _tarefa_nao_encontrada():
    return jsonify(ok=False, error="Tarefa não encontrada."), 404


@app.route("/tarefas")
@student_required
def tarefas():
    return render_template(
        "tasks/index.html",
        tasks=TaskService.listar(current_user.id),
        counts=TaskService.contar(current_user.id),
        prioridades=Task.PRIORIDADES,
        status_opcoes=Task.STATUS,
    )


@app.route("/api/tarefas", methods=["POST"])
@api_student_required
def api_criar_tarefa():
    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400

    formulario = TaskForm()
    if not formulario.validate():
        return _erros_do_formulario(formulario)

    task = TaskService.criar(current_user.id, formulario)
    return _resposta_tarefa(task, 201)


@app.route("/api/tarefas/<int:task_id>", methods=["PUT"])
@api_student_required
def api_editar_tarefa(task_id):
    task = _tarefa_ou_404(task_id)
    if task is None:
        return _tarefa_nao_encontrada()

    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400

    formulario = TaskForm()
    if not formulario.validate():
        return _erros_do_formulario(formulario)

    TaskService.atualizar(task, formulario)
    return _resposta_tarefa(task)


@app.route("/api/tarefas/<int:task_id>/concluir", methods=["PATCH"])
@api_student_required
def api_alternar_tarefa(task_id):
    task = _tarefa_ou_404(task_id)
    if task is None:
        return _tarefa_nao_encontrada()

    TaskService.alternar_conclusao(task)
    return _resposta_tarefa(task)


@app.route("/api/tarefas/<int:task_id>", methods=["DELETE"])
@api_student_required
def api_excluir_tarefa(task_id):
    task = _tarefa_ou_404(task_id)
    if task is None:
        return _tarefa_nao_encontrada()

    TaskService.remover(task)
    return jsonify(ok=True, counts=TaskService.contar(current_user.id))


# ---------------------------------------------------------------------------
# Metas
#   /metas                 -> página (HTML renderizado pelo Jinja)
#   /api/metas/...         -> rotas JSON chamadas via AJAX (fetch) pela página
# ---------------------------------------------------------------------------

def _resposta_meta(goal, status=200):
    """JSON com a meta, o card já renderizado (Jinja) e os contadores."""
    return jsonify(
        ok=True,
        goal=goal.to_dict(),
        html=render_template("goals/_goal_card.html", g=goal),
        counts=GoalService.contar(current_user.id),
    ), status


def _meta_nao_encontrada():
    return jsonify(ok=False, error="Meta não encontrada."), 404


@app.route("/metas")
@student_required
def metas():
    return render_template(
        "goals/index.html",
        goals=GoalService.listar(current_user.id),
        counts=GoalService.contar(current_user.id),
        tipos=Goal.TIPOS,
    )


@app.route("/api/metas", methods=["POST"])
@api_student_required
def api_criar_meta():
    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400

    formulario = GoalForm()
    if not formulario.validate():
        return _erros_do_formulario(formulario)

    goal = GoalService.criar(current_user.id, formulario)
    return _resposta_meta(goal, 201)


@app.route("/api/metas/<int:goal_id>", methods=["PUT"])
@api_student_required
def api_editar_meta(goal_id):
    goal = GoalService.buscar(goal_id, current_user.id)
    if goal is None:
        return _meta_nao_encontrada()

    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400

    formulario = GoalForm()
    if not formulario.validate():
        return _erros_do_formulario(formulario)

    GoalService.atualizar(goal, formulario)
    return _resposta_meta(goal)


@app.route("/api/metas/<int:goal_id>/concluir", methods=["PATCH"])
@api_student_required
def api_concluir_meta(goal_id):
    goal = GoalService.buscar(goal_id, current_user.id)
    if goal is None:
        return _meta_nao_encontrada()

    GoalService.concluir(goal)
    return _resposta_meta(goal)


@app.route("/api/metas/<int:goal_id>", methods=["DELETE"])
@api_student_required
def api_excluir_meta(goal_id):
    goal = GoalService.buscar(goal_id, current_user.id)
    if goal is None:
        return _meta_nao_encontrada()

    GoalService.remover(goal)
    return jsonify(ok=True, counts=GoalService.contar(current_user.id))


# ---------------------------------------------------------------------------
# Cronograma
#   /cronograma            -> página (HTML renderizado pelo Jinja)
#   /api/cronograma/...    -> rotas JSON chamadas via AJAX (fetch) pela página
#
# Diferente de Tarefas e Metas, a resposta da API traz o QUADRO inteiro já
# renderizado (grade da semana + lista por dia), porque adicionar ou mover um
# bloco muda a posição de vários elementos na tela.
# ---------------------------------------------------------------------------

MSG_CONFLITO = "Conflito de horário com outro bloco neste dia."


def _contexto_cronograma():
    itens = ScheduleService.listar(current_user.id)
    return dict(
        total=len(itens),
        por_dia=ScheduleService.agrupar_por_dia(itens),
        dias=ScheduleItem.DIAS,
        horas=range(ScheduleItem.GRADE_INICIO.hour, ScheduleItem.GRADE_FIM.hour),
        altura_hora=ScheduleItem.ALTURA_HORA,
        hoje=date.today().weekday(),
    )


def _resposta_cronograma(item=None, status=200):
    dados = dict(
        ok=True,
        html=render_template("schedule/_board.html", **_contexto_cronograma()),
        counts=ScheduleService.contar(current_user.id),
    )
    if item is not None:
        dados["item"] = item.to_dict()
    return jsonify(dados), status


def _bloco_nao_encontrado():
    return jsonify(ok=False, error="Horário não encontrado."), 404


@app.route("/cronograma")
@student_required
def cronograma():
    return render_template(
        "schedule/index.html",
        cores=ScheduleItem.CORES,
        **_contexto_cronograma(),
    )


@app.route("/api/cronograma", methods=["POST"])
@api_student_required
def api_criar_horario():
    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400

    formulario = ScheduleForm()
    if not formulario.validate():
        return _erros_do_formulario(formulario)
    if ScheduleService.tem_conflito(current_user.id, formulario):
        return jsonify(ok=False, error=MSG_CONFLITO), 409

    item = ScheduleService.criar(current_user.id, formulario)
    return _resposta_cronograma(item, 201)


@app.route("/api/cronograma/<int:item_id>", methods=["PUT"])
@api_student_required
def api_editar_horario(item_id):
    item = ScheduleService.buscar(item_id, current_user.id)
    if item is None:
        return _bloco_nao_encontrado()

    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400

    formulario = ScheduleForm()
    if not formulario.validate():
        return _erros_do_formulario(formulario)
    # ignora o próprio bloco: editar sem mudar o horário não pode dar conflito
    if ScheduleService.tem_conflito(current_user.id, formulario, ignorar_id=item.id):
        return jsonify(ok=False, error=MSG_CONFLITO), 409

    ScheduleService.atualizar(item, formulario)
    return _resposta_cronograma(item)


@app.route("/api/cronograma/<int:item_id>", methods=["DELETE"])
@api_student_required
def api_excluir_horario(item_id):
    item = ScheduleService.buscar(item_id, current_user.id)
    if item is None:
        return _bloco_nao_encontrado()

    ScheduleService.remover(item)
    return _resposta_cronograma()


# ---------------------------------------------------------------------------
# Pontos (mostrados no topo e na barra lateral de todas as telas do aluno)
# ---------------------------------------------------------------------------

@app.context_processor
def injetar_pontos():
    """Deixa a variável `pontos_total` disponível em todos os templates."""
    usuario = current_user._get_current_object() if current_user else None
    if isinstance(usuario, Student):
        return {"pontos_total": PointsService.total(usuario.id)}
    return {"pontos_total": 0}


# ---------------------------------------------------------------------------
# Pomodoro
#   /pomodoro                      -> página (o cronômetro roda no navegador)
#   /api/pomodoro/iniciar          -> abre uma sessão de foco no servidor
#   /api/pomodoro/<id>/concluir    -> confere o tempo e dá os pontos
#   /api/pomodoro/<id>/cancelar    -> descarta a sessão (reiniciar / trocar de modo)
# ---------------------------------------------------------------------------

def _sessao_nao_encontrada():
    return jsonify(ok=False, error="Sessão não encontrada."), 404


def _historico_html():
    return render_template(
        "pomodoro/_history.html", sessoes=PomodoroService.ultimas(current_user.id)
    )


@app.route("/pomodoro")
@student_required
def pomodoro():
    return render_template(
        "pomodoro/index.html",
        hoje=PomodoroService.resumo_do_dia(current_user.id),
        sessoes=PomodoroService.ultimas(current_user.id),
        limites=PomodoroSession,
    )


@app.route("/api/pomodoro/iniciar", methods=["POST"])
@api_student_required
def api_iniciar_pomodoro():
    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400

    formulario = PomodoroForm()
    if not formulario.validate():
        return _erros_do_formulario(formulario)

    sessao = PomodoroService.iniciar(current_user.id, formulario.minutos)
    return jsonify(ok=True, session=sessao.to_dict()), 201


@app.route("/api/pomodoro/<int:sessao_id>/concluir", methods=["POST"])
@api_student_required
def api_concluir_pomodoro(sessao_id):
    sessao = PomodoroService.buscar(sessao_id, current_user.id)
    if sessao is None:
        return _sessao_nao_encontrada()

    try:
        pontos = PomodoroService.concluir(sessao)
    except SessaoJaEncerrada as erro:
        return jsonify(ok=False, error=str(erro)), 409
    except PomodoroError as erro:
        return jsonify(ok=False, error=str(erro)), 422

    return jsonify(
        ok=True,
        points_awarded=pontos,
        points_total=PointsService.total(current_user.id),
        today=PomodoroService.resumo_do_dia(current_user.id),
        history_html=_historico_html(),
    )


@app.route("/api/pomodoro/<int:sessao_id>/cancelar", methods=["POST"])
@api_student_required
def api_cancelar_pomodoro(sessao_id):
    sessao = PomodoroService.buscar(sessao_id, current_user.id)
    if sessao is None:
        return _sessao_nao_encontrada()

    PomodoroService.cancelar(sessao)
    return jsonify(ok=True)
