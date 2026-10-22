from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.models.goal import Goal
from app.models.pomodoro_session import PomodoroSession
from app.models.task import Task
from app.services.GoalService import GoalService
from app.services.PointsService import PointsService
from app.services.TaskService import TaskService

FUSO = ZoneInfo("America/Sao_Paulo")
DIAS_CURTOS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]

# ---------------------------------------------------------------------------
# DADOS PROVISÓRIOS (exemplo do protótipo)
# As telas de Física e Ranking ainda não existem. Quando existirem, troque
# estas constantes por consultas reais (ex.: PhysicsService, RankingService).
# ---------------------------------------------------------------------------
TOPICOS_PROVISORIOS = {"concluidos": 3, "total": 10, "resumo": "Cinemática, Óptica..."}
FISICA_PROVISORIA = [
    {"nome": "Cinemática", "emoji": "🚗", "pct": 75},
    {"nome": "Dinâmica", "emoji": "⚡", "pct": 40},
    {"nome": "Energia", "emoji": "🔋", "pct": 20},
]
POSICAO_RANKING_PROVISORIA = 4


def _formatar_data_curta(d):
    return f"{d.day} {MESES[d.month - 1]}"


def _formatar_duracao(minutos):
    h, m = divmod(int(minutos), 60)
    if h and m:
        return f"{h}h {m}min"
    if h:
        return f"{h}h"
    return f"{m}min"


def _rotulo_barra(minutos):
    horas = minutos / 60
    texto = f"{horas:.1f}".replace(".", ",")
    if texto.endswith(",0"):
        texto = texto[:-2]
    return f"{texto}h"


def _para_data(valor):
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    return valor


def _para_local(momento):
    # aceita datas "ingênuas" gravadas em UTC e também com fuso
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(FUSO)


class DashboardService:
    """Reúne tudo que o painel do aluno mostra. Toda consulta filtra por student_id."""

    @staticmethod
    def saudacao(agora=None):
        hora = (agora or datetime.now(FUSO)).hour
        if hora < 12:
            return "Bom dia"
        if hora < 18:
            return "Boa tarde"
        return "Boa noite"

    @staticmethod
    def horas_da_semana(student_id, hoje=None):
        hoje = hoje or datetime.now(FUSO).date()
        segunda = hoje - timedelta(days=hoje.weekday())
        segunda_anterior = segunda - timedelta(days=7)

        inicio_utc = (
            datetime.combine(segunda_anterior, datetime.min.time(), tzinfo=FUSO)
            .astimezone(timezone.utc)
            .replace(tzinfo=None)
        )
        sessoes = PomodoroSession.query.filter(
            PomodoroSession.student_id == student_id,
            PomodoroSession.status == "concluida",
            PomodoroSession.completed_at >= inicio_utc,
        ).all()

        por_dia = [0] * 7
        anterior = 0
        for s in sessoes:
            if s.completed_at is None:
                continue
            dia = _para_local(s.completed_at).date()
            if dia >= segunda:
                if (dia - segunda).days < 7:
                    por_dia[(dia - segunda).days] += s.minutes
            elif dia >= segunda_anterior:
                anterior += s.minutes

        total = sum(por_dia)
        maior = max(por_dia) or 1
        barras = [
            {
                "dia": DIAS_CURTOS[i],
                "rotulo": _rotulo_barra(m),
                "pct": round(m / maior * 100) if m else 0,
                "hoje": i == hoje.weekday(),
            }
            for i, m in enumerate(por_dia)
        ]

        diferenca = total - anterior
        if anterior == 0 and total == 0:
            comparacao = "Sem estudos registrados ainda"
        elif anterior == 0:
            comparacao = "Primeira semana com registros"
        else:
            sinal = "+" if diferenca >= 0 else "−"
            comparacao = f"{sinal}{_formatar_duracao(abs(diferenca))} vs. semana passada"

        variacao = None
        if anterior > 0:
            variacao = round(diferenca / anterior * 100)

        return {
            "total": _formatar_duracao(total),
            "comparacao": comparacao,
            "barras": barras,
            "variacao": variacao,
        }

    @staticmethod
    def proximas_tarefas(student_id, limite=3, hoje=None):
        hoje = hoje or datetime.now(FUSO).date()
        tarefas = (
            Task.query.filter(Task.student_id == student_id, Task.status != "concluida")
            .order_by(Task.due_date, Task.id)
            .limit(limite)
            .all()
        )
        itens = []
        for t in tarefas:
            prazo = _para_data(t.due_date)
            if prazo is None:
                rotulo, tom = "Sem prazo", "ok"
            else:
                dias = (prazo - hoje).days
                if dias < 0:
                    rotulo, tom = "Atrasada", "alta"
                elif dias == 0:
                    rotulo, tom = "Hoje", "alta"
                elif dias == 1:
                    rotulo, tom = "Amanhã", "media"
                else:
                    rotulo, tom = _formatar_data_curta(prazo), "ok"
            itens.append({
                "titulo": t.title,
                "disciplina": t.subject,
                "rotulo": rotulo,
                "tom": tom,
            })
        return itens

    @staticmethod
    def prazo_das_metas(student_id):
        abertas = [
            g for g in GoalService.listar(student_id) if not g.is_done and g.due_date
        ]
        if not abertas:
            return "Nenhuma meta em aberto"
        proxima = min(_para_data(g.due_date) for g in abertas)
        return f"Prazo: {_formatar_data_curta(proxima)}"

    @staticmethod
    def montar(student):
        sid = student.id
        tarefas = TaskService.contar(sid)
        metas = GoalService.contar(sid)
        semana = DashboardService.horas_da_semana(sid)

        return {
            "primeiro_nome": student.name.split()[0],
            "saudacao": DashboardService.saudacao(),
            "semana": semana,
            "tarefas": {
                "concluidas": tarefas["concluida"],
                "total": tarefas["todas"],
                "pendentes": tarefas["abertas"],
            },
            "metas": {
                "concluidas": metas["concluidas"],
                "total": metas["todas"],
                "prazo": DashboardService.prazo_das_metas(sid),
            },
            "topicos": TOPICOS_PROVISORIOS,          # provisório
            "pontos": PointsService.total(sid),
            "posicao": POSICAO_RANKING_PROVISORIA,   # provisório
            "proximas": DashboardService.proximas_tarefas(sid),
            "fisica": FISICA_PROVISORIA,             # provisório
        }