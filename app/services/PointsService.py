from sqlalchemy import func

from app import db
from app.models.point_transaction import PointTransaction


class PointsService:
    @staticmethod
    def total(student_id):
        soma = (
            db.session.query(func.coalesce(func.sum(PointTransaction.amount), 0))
            .filter(PointTransaction.student_id == student_id)
            .scalar()
        )
        return int(soma)

    @staticmethod
    def conceder(student_id, quantidade, motivo, ref_id=None):
        """Adiciona o lançamento na sessão do banco. Quem chama faz o commit,
        assim os pontos e o evento que os gerou são gravados juntos."""
        lancamento = PointTransaction(
            student_id=student_id, amount=quantidade, reason=motivo, ref_id=ref_id
        )
        db.session.add(lancamento)
        return lancamento
