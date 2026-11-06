from datetime import date
from secrets import token_urlsafe
from flask import abort, jsonify, redirect, render_template, request, session, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from app.forms.login_form import LoginForm
from app.forms.student_form import RegistrationForm
from app.forms.task_form import TaskForm
from app.forms.goal_form import GoalForm
from app.forms.schedule_form import ScheduleForm
from app.forms.pomodoro_form import PomodoroForm
from app.forms.physics_form import (
    ActionForm,
    PhysicsResourceForm,
    PhysicsTopicContentForm,
    QuizForm,
    QuizQuestionForm,
)
from app.decorators import api_student_required, professor_required, student_required
from app.models.task import Task
from app.models.goal import Goal
from app.models.schedule_item import ScheduleItem
from app.models.student import Student
from app.models.pomodoro_session import PomodoroSession
from app.models.physics import Quiz, QuizOption, QuizQuestion, PhysicsTopic
from app.services.TaskService import TaskService
from app.services.GoalService import GoalService
from app.services.ScheduleService import ScheduleService
from app.services.PointsService import PointsService
from app.services.PomodoroService import PomodoroService, PomodoroError, SessaoJaEncerrada
from app.services.StudentService import StudentService
from app.services.ProfessorService import ProfessorService
from app.services.AuthService import AuthService, SuapAuthError
from app.services.DashboardService import DashboardService
from app.services.QuizService import QuizService, QuizError
from app.services.PhysicsService import PhysicsService
from app.services.PhysicsResourceService import PhysicsResourceService, ResourceError

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
    state = token_urlsafe(32)
    redirect_uri = url_for("login_suap_callback", _external=True)
    session["suap_oauth_state"] = state
    try:
        authorization_url = AuthService.get_authorization_url(redirect_uri, state)
    except RuntimeError:
        flash(
            "O login com o SUAP ainda não foi configurado. Defina "
            "SUAP_CLIENT_ID e SUAP_CLIENT_SECRET no arquivo .env e cadastre "
            "a URL de retorno indicada no README.",
            "warning",
        )
        return redirect(url_for("login"))
 
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
 
    code = request.args.get("code")
    if not code:
        flash("O SUAP não enviou o código de autorização. Tente novamente.", "danger")
        return redirect(url_for("login"))

    try:
        redirect_uri = url_for("login_suap_callback", _external=True)
        dados_suap = AuthService.get_user_data(code, redirect_uri)
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
 
    formulario = RegistrationForm()
 
    if formulario.validate_on_submit():
        if formulario.profile_type.data == "professor":
            usuario = ProfessorService.salvar(formulario)
            papel = "professor"
        else:
            usuario = StudentService.salvar(formulario)
            papel = "aluno"
        login_user(usuario)
        flash(f"Cadastro de {papel} concluído! Bem-vindo(a), {usuario.name}.", "success")
        return redirect(url_for("index"))
 
    return render_template("student/signin.html", formulario=formulario)


# ---------------------------------------------------------------------------
# Física: catálogo de tópicos e conteúdo teórico para alunos e professores
# ---------------------------------------------------------------------------

@app.route("/fisica")
@login_required
def fisica():
    usuario = current_user._get_current_object()
    student_id = usuario.id if isinstance(usuario, Student) else None
    topicos = PhysicsService.listar_topicos(student_id)
    concluidos = sum(1 for item in topicos if item["concluido"])
    return render_template(
        "physics/index.html",
        topicos=topicos,
        total_concluidos=concluidos,
        total_topicos=len(topicos),
    )


@app.route("/fisica/topicos/<slug>")
@login_required
def topico_fisica(slug):
    usuario = current_user._get_current_object()
    student_id = usuario.id if isinstance(usuario, Student) else None
    topico, concluido = PhysicsService.buscar_topico(slug, student_id)
    if topico is None:
        flash("Tópico não encontrado.", "warning")
        return redirect(url_for("fisica"))
    recursos = PhysicsResourceService.recursos_publicos(topico.id)
    simulados = (
        Quiz.query.filter_by(topic_id=topico.id, is_active=True)
        .filter(Quiz.questions.any())
        .order_by(Quiz.id.desc())
        .all()
    )
    return render_template(
        "physics/topic.html",
        topico=topico,
        concluido=concluido,
        pode_concluir=isinstance(usuario, Student),
        recursos=recursos,
        simulados=simulados,
    )


@app.route("/fisica/topicos/<slug>/concluir", methods=["POST"])
@student_required
def concluir_topico_fisica(slug):
    topico = PhysicsTopic.query.filter_by(slug=slug).first()
    if topico is None:
        flash("Tópico não encontrado.", "warning")
        return redirect(url_for("fisica"))
    novo = PhysicsService.concluir_topico(current_user.id, topico.id)
    flash(
        "Tópico marcado como concluído!" if novo else "Este tópico já estava concluído.",
        "success" if novo else "info",
    )
    return redirect(url_for("topico_fisica", slug=slug))


@app.route("/professor/conteudos")
@professor_required
def gerenciar_conteudos():
    return render_template(
        "physics/manage.html",
        topicos=PhysicsService.listar_topicos(),
    )


@app.route("/professor/conteudos/<int:topic_id>/editar", methods=["GET", "POST"])
@professor_required
def editar_conteudo_fisica(topic_id):
    topico = db.session.get(PhysicsTopic, topic_id)
    if topico is None:
        abort(404)

    formulario = PhysicsTopicContentForm(obj=topico)
    if formulario.validate_on_submit():
        topico.summary = formulario.summary.data.strip()
        topico.content = formulario.content.data.strip()
        topico.solved_example = (formulario.solved_example.data or "").strip() or None
        db.session.commit()
        flash("Conteúdo do tópico atualizado.", "success")
        return redirect(url_for("gerenciar_conteudos"))

    return render_template("physics/topic_form.html", topico=topico, formulario=formulario)


def _pagina_materiais_publicos(topico, formulario, material_em_edicao=None):
    return render_template(
        "physics/resources.html",
        topico=topico,
        formulario=formulario,
        material_em_edicao=material_em_edicao,
        formulario_acao=ActionForm(),
        materiais=PhysicsResourceService.listar_para_gerencia(topico.id),
    )


@app.route(
    "/professor/conteudos/<int:topic_id>/materiais",
    defaults={"resource_id": None},
    methods=["GET", "POST"],
)
@app.route(
    "/professor/conteudos/<int:topic_id>/materiais/<int:resource_id>",
    methods=["GET", "POST"],
)
@professor_required
def gerenciar_materiais_fisica(topic_id, resource_id):
    topico = db.session.get(PhysicsTopic, topic_id)
    if topico is None:
        abort(404)
    material = (
        PhysicsResourceService.buscar_para_gerencia(resource_id, topic_id)
        if resource_id is not None
        else None
    )
    if resource_id is not None and material is None:
        abort(404)

    formulario = PhysicsResourceForm(obj=material)
    if formulario.validate_on_submit():
        try:
            PhysicsResourceService.salvar_publico(
                topic_id=topico.id,
                title=formulario.title.data,
                description=formulario.description.data,
                url=formulario.url.data,
                resource=material,
            )
        except ResourceError as erro:
            formulario.url.errors.append(str(erro))
        else:
            flash("Material publicado para todos os alunos.", "success")
            return redirect(
                url_for("gerenciar_materiais_fisica", topic_id=topico.id)
            )

    return _pagina_materiais_publicos(topico, formulario, material)


@app.route(
    "/professor/conteudos/<int:topic_id>/materiais/<int:resource_id>/remover",
    methods=["POST"],
)
@professor_required
def remover_material_fisica(topic_id, resource_id):
    topico = db.session.get(PhysicsTopic, topic_id)
    material = PhysicsResourceService.buscar_para_gerencia(resource_id, topic_id)
    formulario = ActionForm()
    if topico is None or material is None:
        abort(404)
    if formulario.validate_on_submit():
        PhysicsResourceService.remover_material(material)
        flash("Material removido da aba de Física.", "success")
    return redirect(url_for("gerenciar_materiais_fisica", topic_id=topic_id))


@app.route("/professor/conteudos/<int:topic_id>/simulados", methods=["GET", "POST"])
@professor_required
def gerenciar_simulados_fisica(topic_id):
    topico = db.session.get(PhysicsTopic, topic_id)
    if topico is None:
        abort(404)
    formulario = QuizForm()
    if formulario.validate_on_submit():
        simulado = Quiz(
            topic_id=topico.id,
            title=formulario.title.data.strip(),
            points_per_correct=formulario.points_per_correct.data,
            is_active=formulario.is_active.data,
        )
        db.session.add(simulado)
        db.session.commit()
        flash("Simulado criado. Agora adicione as questões.", "success")
        return redirect(url_for("editar_simulado_fisica", quiz_id=simulado.id))

    simulados = Quiz.query.filter_by(topic_id=topico.id).order_by(Quiz.id.desc()).all()
    return render_template(
        "physics/quizzes.html",
        topico=topico,
        formulario=formulario,
        simulados=simulados,
    )


@app.route("/professor/simulados/<int:quiz_id>", methods=["GET", "POST"])
@professor_required
def editar_simulado_fisica(quiz_id):
    simulado = db.session.get(Quiz, quiz_id)
    if simulado is None:
        abort(404)
    formulario = QuizForm(obj=simulado)
    if formulario.validate_on_submit():
        simulado.title = formulario.title.data.strip()
        simulado.points_per_correct = formulario.points_per_correct.data
        simulado.is_active = formulario.is_active.data
        db.session.commit()
        flash("Configurações do simulado salvas.", "success")
        return redirect(url_for("editar_simulado_fisica", quiz_id=simulado.id))

    questoes = simulado.questions.order_by(QuizQuestion.position, QuizQuestion.id).all()
    return render_template(
        "physics/quiz_form.html",
        simulado=simulado,
        formulario=formulario,
        questoes=questoes,
    )


@app.route(
    "/professor/simulados/<int:quiz_id>/questoes/nova",
    defaults={"question_id": None},
    methods=["GET", "POST"],
)
@app.route(
    "/professor/simulados/<int:quiz_id>/questoes/<int:question_id>",
    methods=["GET", "POST"],
)
@professor_required
def editar_questao_simulado(quiz_id, question_id):
    simulado = db.session.get(Quiz, quiz_id)
    if simulado is None:
        abort(404)
    questao = (
        db.session.get(QuizQuestion, question_id)
        if question_id is not None
        else None
    )
    if question_id is not None and (questao is None or questao.quiz_id != simulado.id):
        abort(404)

    formulario = QuizQuestionForm()
    opcoes = (
        questao.options.order_by(QuizOption.position, QuizOption.id).all()
        if questao is not None
        else []
    )
    if request.method == "GET" and questao is not None:
        formulario.prompt.data = questao.prompt
        formulario.explanation.data = questao.explanation
        fields = [formulario.option_a, formulario.option_b, formulario.option_c, formulario.option_d]
        for field, option in zip(fields, opcoes[:4]):
            field.data = option.text
        correta = next((i + 1 for i, option in enumerate(opcoes[:4]) if option.is_correct), 1)
        formulario.correct_option.data = str(correta)

    if formulario.validate_on_submit():
        if formulario.correct_option.data == "0":
            formulario.correct_option.errors.append("Marque a alternativa correta.")
        else:
            if questao is None:
                questao = QuizQuestion(
                    quiz_id=simulado.id,
                    position=simulado.questions.count() + 1,
                )
                db.session.add(questao)
                db.session.flush()

            questao.prompt = formulario.prompt.data.strip()
            questao.explanation = (formulario.explanation.data or "").strip() or None
            questao.position = questao.position or simulado.questions.count()
            fields = [formulario.option_a, formulario.option_b, formulario.option_c, formulario.option_d]
            for index, field in enumerate(fields):
                if index < len(opcoes):
                    option = opcoes[index]
                else:
                    option = QuizOption(question_id=questao.id, position=index + 1)
                    db.session.add(option)
                option.text = field.data.strip()
                option.position = index + 1
                option.is_correct = formulario.correct_option.data == str(index + 1)
            for option in opcoes[4:]:
                option.is_correct = False
            db.session.commit()
            flash("Questão salva.", "success")
            return redirect(url_for("editar_simulado_fisica", quiz_id=simulado.id))

    return render_template(
        "physics/question_form.html",
        simulado=simulado,
        questao=questao,
        formulario=formulario,
    )


@app.route("/fisica/simulados/<int:quiz_id>", methods=["GET", "POST"])
@student_required
def responder_simulado(quiz_id):
    simulado = Quiz.query.filter_by(id=quiz_id, is_active=True).first_or_404()
    questoes = simulado.questions.order_by(QuizQuestion.position, QuizQuestion.id).all()
    if not questoes:
        flash("Este simulado ainda não tem questões.", "warning")
        return redirect(url_for("topico_fisica", slug=simulado.topic.slug))

    formulario_acao = ActionForm()
    respostas_marcadas = {
        questao.id: request.form.get(f"question_{questao.id}")
        for questao in questoes
    } if request.method == "POST" else {}
    if request.method == "POST" and formulario_acao.validate_on_submit():
        faltantes = [
            questao for questao in questoes
            if not respostas_marcadas.get(questao.id)
        ]
        if faltantes:
            flash("Responda a todas as questões antes de enviar.", "warning")
        else:
            try:
                tentativa = QuizService.iniciar_tentativa(current_user.id, simulado.id)
                resultado = QuizService.enviar_respostas(
                    tentativa.id,
                    current_user.id,
                    respostas_marcadas,
                )
            except QuizError as erro:
                flash(str(erro), "warning")
            else:
                detalhes_respostas = []
                for questao in questoes:
                    opcoes = questao.options.order_by(QuizOption.position, QuizOption.id).all()
                    marcada = next(
                        (opcao for opcao in opcoes if str(opcao.id) == respostas_marcadas[questao.id]),
                        None,
                    )
                    correta = next((opcao for opcao in opcoes if opcao.is_correct), None)
                    detalhes_respostas.append({
                        "questao": questao,
                        "marcada": marcada,
                        "correta": correta,
                        "explicacao": questao.explanation,
                        "acertou": bool(marcada and marcada.is_correct),
                    })
                return render_template(
                    "physics/quiz_take.html",
                    simulado=simulado,
                    questoes=questoes,
                    formulario_acao=formulario_acao,
                    respostas_marcadas={},
                    resultado=resultado,
                    detalhes_respostas=detalhes_respostas,
                )

    return render_template(
        "physics/quiz_take.html",
        simulado=simulado,
        questoes=questoes,
        formulario_acao=formulario_acao,
        respostas_marcadas=respostas_marcadas,
        resultado=None,
        detalhes_respostas=[],
    )


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


# ---------------------------------------------------------------------------
# Quizzes: API para servir questões, registrar tentativas e pontuar a primeira
# resposta de cada aluno para cada questão.
# ---------------------------------------------------------------------------

@app.route("/api/quizzes/<int:quiz_id>")
@api_student_required
def api_obter_quiz(quiz_id):
    quiz = Quiz.query.filter_by(id=quiz_id, is_active=True).first()
    if quiz is None:
        return jsonify(ok=False, error="Quiz não encontrado."), 404

    questoes = QuizQuestion.query.filter_by(quiz_id=quiz.id).order_by(QuizQuestion.position).all()
    return jsonify(
        ok=True,
        quiz={
            "id": quiz.id,
            "title": quiz.title,
            "points_per_correct": quiz.points_per_correct,
            "topic": {
                "id": quiz.topic.id,
                "title": quiz.topic.title,
                "unit": {"id": quiz.topic.unit.id, "name": quiz.topic.unit.name},
            },
            "questions": [
                {
                    "id": question.id,
                    "prompt": question.prompt,
                    "position": question.position,
                    "options": [
                        {"id": option.id, "text": option.text, "position": option.position}
                        for option in question.options.all()
                    ],
                }
                for question in questoes
            ],
        },
    )


@app.route("/api/quizzes/<int:quiz_id>/tentativas", methods=["POST"])
@api_student_required
def api_iniciar_tentativa_quiz(quiz_id):
    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(ok=False, error="Envie os dados em formato JSON."), 400
    try:
        tentativa = QuizService.iniciar_tentativa(current_user.id, quiz_id)
    except QuizError as erro:
        return jsonify(ok=False, error=str(erro)), 404
    return jsonify(ok=True, attempt_id=tentativa.id, started_at=tentativa.started_at), 201


@app.route("/api/quizzes/tentativas/<int:attempt_id>/respostas", methods=["POST"])
@api_student_required
def api_enviar_respostas_quiz(attempt_id):
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not isinstance(dados.get("answers"), dict):
        return jsonify(ok=False, error="Envie as respostas em um objeto JSON `answers`."), 400
    try:
        resultado = QuizService.enviar_respostas(
            attempt_id=attempt_id,
            student_id=current_user.id,
            respostas=dados["answers"],
        )
    except QuizError as erro:
        return jsonify(ok=False, error=str(erro)), 422

    resultado["points_total"] = PointsService.total(current_user.id)
    return jsonify(ok=True, result=resultado)
