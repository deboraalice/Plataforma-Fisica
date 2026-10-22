"""
Datas e horas da plataforma.

O banco guarda sempre em UTC (sem fuso). Para decidir o que é "hoje" ou mostrar
um horário ao aluno, convertemos para o horário de Brasília/Ceará (UTC-3).
O Brasil não tem horário de verão desde 2019, então um deslocamento fixo basta
e evita depender do pacote tzdata no Windows.
"""
from datetime import datetime, timedelta, timezone

FUSO_LOCAL = timezone(timedelta(hours=-3))


def agora_utc():
    """Agora em UTC, no mesmo formato que o banco usa (datetime sem fuso)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def para_local(momento_utc):
    return momento_utc.replace(tzinfo=timezone.utc).astimezone(FUSO_LOCAL)


def inicio_do_dia_utc(referencia_utc=None):
    """Meia-noite de hoje (no horário local), convertida para UTC."""
    local = para_local(referencia_utc or agora_utc())
    meia_noite = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return meia_noite.astimezone(timezone.utc).replace(tzinfo=None)


def descrever_quando(momento_utc):
    """'Hoje, 14:30' / 'Ontem, 09:10' / '12/10, 08:00' (no horário local)."""
    local = para_local(momento_utc)
    hoje = para_local(agora_utc()).date()
    hora = local.strftime("%H:%M")
    if local.date() == hoje:
        return f"Hoje, {hora}"
    if local.date() == hoje - timedelta(days=1):
        return f"Ontem, {hora}"
    return f"{local.strftime('%d/%m')}, {hora}"
