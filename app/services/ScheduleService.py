from app import db
from app.models.schedule_item import ScheduleItem

class ScheduleService:
    """Toda consulta filtra por student_id: cada aluno só vê o próprio cronograma."""

    @staticmethod
    def listar(student_id):
        return (
            ScheduleItem.query.filter_by(student_id=student_id)
            .order_by(ScheduleItem.weekday, ScheduleItem.start_time)
            .all()
        )

    @staticmethod
    def buscar(item_id, student_id):
        return ScheduleItem.query.filter_by(id=item_id, student_id=student_id).first()

    @staticmethod
    def contar(student_id):
        return {"total": ScheduleItem.query.filter_by(student_id=student_id).count()}

    @staticmethod
    def agrupar_por_dia(itens):
        """Lista com 7 posições (segunda a domingo), cada uma com os blocos do dia."""
        por_dia = [[] for _ in ScheduleItem.DIAS]
        for item in itens:
            por_dia[item.weekday].append(item)
        return por_dia

    @staticmethod
    def tem_conflito(student_id, formulario, ignorar_id=None):
        """
        Dois blocos do mesmo dia conflitam quando um começa antes de o outro
        terminar E termina depois de o outro começar. Blocos "encostados"
        (um termina às 10:00 e o outro começa às 10:00) NÃO são conflito.
        """
        consulta = ScheduleItem.query.filter(
            ScheduleItem.student_id == student_id,
            ScheduleItem.weekday == formulario.dia,
            ScheduleItem.start_time < formulario.fim,
            ScheduleItem.end_time > formulario.inicio,
        )
        if ignorar_id is not None:
            consulta = consulta.filter(ScheduleItem.id != ignorar_id)
        return consulta.first() is not None

    @staticmethod
    def criar(student_id, formulario):
        item = ScheduleItem(student_id=student_id)
        ScheduleService._preencher(item, formulario)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def atualizar(item, formulario):
        ScheduleService._preencher(item, formulario)
        db.session.commit()
        return item

    @staticmethod
    def remover(item):
        db.session.delete(item)
        db.session.commit()

    @staticmethod
    def _preencher(item, formulario):
        item.subject = formulario.subject.data
        item.weekday = formulario.dia
        item.start_time = formulario.inicio
        item.end_time = formulario.fim
        item.color = formulario.color.data
