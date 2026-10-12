from sqlalchemy.exc import IntegrityError

from app import db
from app.models.point_transaction import PointTransaction
from app.models.pomodoro_session import PomodoroSession
from app.services.PointsService import PointsService
from app.timeutils import agora_utc, inicio_do_dia_utc


class PomodoroError(Exception):
    """Erro de regra de negócio; a mensagem pode ser mostrada ao aluno."""


class SessaoJaEncerrada(PomodoroError):
    pass


class TempoNaoCompleto(PomodoroError):
    pass


class PomodoroService:
    """Toda consulta filtra por student_id: cada aluno só mexe nas próprias sessões."""

    @staticmethod
    def buscar(sessao_id, student_id):
        return PomodoroSession.query.filter_by(id=sessao_id, student_id=student_id).first()

    @staticmethod
    def iniciar(student_id, minutos):
        # só pode haver uma sessão aberta por aluno: as antigas (de uma aba
        # fechada, por exemplo) são canceladas
        PomodoroSession.query.filter_by(
            student_id=student_id, status="em_andamento"
        ).update({"status": "cancelada"})

        sessao = PomodoroSession(student_id=student_id, minutes=minutos)
        db.session.add(sessao)
        db.session.commit()
        return sessao

    @staticmethod
    def cancelar(sessao):
        if sessao.status == "em_andamento":
            sessao.status = "cancelada"
            db.session.commit()

    @staticmethod
    def concluir(sessao, agora=None):
        """
        Confirma a sessão e dá os pontos. O cronômetro roda no navegador, então
        o servidor confere o relógio dele: sem o tempo completo, não há pontos.
        """
        agora = agora or agora_utc()

        if sessao.status != "em_andamento":
            raise SessaoJaEncerrada("Esta sessão já foi encerrada.")
        if not sessao.tempo_completo(agora):
            raise TempoNaoCompleto("O tempo da sessão ainda não terminou.")

        pontos = PomodoroSession.pontos_para(sessao.minutes)
        sessao.status = "concluida"
        sessao.completed_at = agora
        sessao.points_awarded = pontos
        PointsService.conceder(sessao.student_id, pontos, PointTransaction.POMODORO, sessao.id)

        try:
            db.session.commit()
        except IntegrityError:
            # duas requisições concluíram a mesma sessão ao mesmo tempo
            db.session.rollback()
            raise SessaoJaEncerrada("Esta sessão já foi encerrada.")
        return pontos

    @staticmethod
    def resumo_do_dia(student_id):
        concluidas = PomodoroSession.query.filter(
            PomodoroSession.student_id == student_id,
            PomodoroSession.status == "concluida",
            PomodoroSession.completed_at >= inicio_do_dia_utc(),
        ).all()
        return {
            "sessions": len(concluidas),
            "points": sum(s.points_awarded for s in concluidas),
        }

    @staticmethod
    def ultimas(student_id, quantidade=5):
        return (
            PomodoroSession.query.filter_by(student_id=student_id, status="concluida")
            .order_by(PomodoroSession.completed_at.desc(), PomodoroSession.id.desc())
            .limit(quantidade)
            .all()
        )
