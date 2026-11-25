"""Aplica as alterações de metas globais em app/routes.py e
app/services/DashboardService.py. Rode na raiz do projeto:
    python aplicar_metas.py
Falha sem alterar nada se algum trecho esperado não for encontrado."""
from pathlib import Path

ROTAS = Path("app/routes.py")
DASH = Path("app/services/DashboardService.py")

NOVO_BLOCO_METAS = '''@app.before_request
def registrar_acesso_diario():
    """Alimenta a meta de presença: no máximo uma escrita por dia por sessão."""
    if request.endpoint in (None, "static") or not current_user.is_authenticated:
        return
    usuario = current_user._get_current_object()
    if not isinstance(usuario, Student):
        return
    hoje = datetime.now(FUSO).date()
    if session.get("ultimo_acesso") == hoje.isoformat():
        return
    GoalService.registrar_acesso(usuario.id, hoje)
    session["ultimo_acesso"] = hoje.isoformat()


def _resposta_metas(points_awarded=0):
    return jsonify(
        ok=True,
        html=render_template("goals/_lista.html", metas=GoalService.listar(current_user.id)),
        counts=GoalService.contar(current_user.id),
        points_total=PointsService.total(current_user.id),
        points_awarded=points_awarded,
    )


@app.route("/metas")
@student_required
def metas():
    return render_template(
        "goals/index.html",
        metas=GoalService.listar(current_user.id),
        counts=GoalService.contar(current_user.id),
    )


@app.route("/api/metas/<key>/resgatar", methods=["POST"])
@api_student_required
def api_resgatar_meta(key):
    try:
        pontos = GoalService.resgatar(current_user.id, key)
    except GoalError as erro:
        return jsonify(ok=False, error=str(erro)), 409
    return _resposta_metas(points_awarded=pontos)


'''

NOVO_PRAZO = '''    @staticmethod
    def prazo_das_metas(student_id):
        cartoes = GoalService.listar(student_id)
        prontas = sum(c["prontos"] for c in cartoes)
        if prontas:
            return f"{prontas} recompensa(s) para resgatar"
        abertas = [c for c in cartoes if not c["completa"]]
        if not abertas:
            return "Todas as metas concluídas 🎉"
        c = max(abertas, key=lambda c: c["pct"])
        return f"Próxima: {c['alvo']} {c['unidade']}"

'''


def trocar(texto, antigo, novo):
    if texto.count(antigo) != 1:
        raise SystemExit(f"Trecho não encontrado (ou repetido): {antigo[:60]!r}")
    return texto.replace(antigo, novo)


def cortar(texto, ini, fim, novo):
    i = texto.find(ini)
    j = texto.find(fim, i)
    if i < 0 or j < 0:
        raise SystemExit(f"Marcadores não encontrados: {ini[:40]!r}")
    return texto[:i] + novo + texto[j:]


r = ROTAS.read_text(encoding="utf-8")
r = trocar(r, "from datetime import date\n", "from datetime import date, datetime\n")
r = trocar(r, "from app.forms.goal_form import GoalForm\n", "")
r = trocar(r, "from app.models.goal import Goal\n", "")
r = trocar(r, "from app.services.GoalService import GoalService\n",
           "from app.services.GoalService import GoalService, GoalError\n")
r = trocar(r, "from app.services.DashboardService import DashboardService\n",
           "from app.services.DashboardService import DashboardService, FUSO\n")

# bloco de metas: de _resposta_meta até a linha de traços do cabeçalho "Cronograma"
ini = "def _resposta_meta(goal"
cab = r.find("# Cronograma\n")
fim_marcador = r.rfind("# -----", 0, cab)
if cab < 0 or fim_marcador < 0:
    raise SystemExit("Cabeçalho do Cronograma não encontrado.")
i = r.find(ini)
if i < 0:
    raise SystemExit("Bloco de metas não encontrado.")
r = r[:i] + NOVO_BLOCO_METAS + r[fim_marcador:]

d = DASH.read_text(encoding="utf-8")
d = cortar(d, "    @staticmethod\n    def prazo_das_metas",
           "    @staticmethod\n    def montar", NOVO_PRAZO)

ROTAS.write_text(r, encoding="utf-8")
DASH.write_text(d, encoding="utf-8")
print("OK: routes.py e DashboardService.py atualizados.")