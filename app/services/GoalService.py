from sqlalchemy.exc import IntegrityError

from app import db
from app.models.goal import GoalClaim, StudentActivityDay
from app.models.point_transaction import PointTransaction
from app.services.GoalCatalog import CATALOGO, CATALOGO_POR_CHAVE
from app.services.PointsService import PointsService


class GoalError(Exception):
    pass


class GoalService:
    """Metas globais: o catálogo é igual para todos; o progresso é por aluno."""

    @staticmethod
    def registrar_acesso(student_id, hoje):
        """Marca o dia de hoje como 'aluno presente' (uma linha por dia)."""
        existe = StudentActivityDay.query.filter_by(student_id=student_id, day=hoje).first()
        if existe:
            return
        db.session.add(StudentActivityDay(student_id=student_id, day=hoje))
        try:
            db.session.commit()
        except IntegrityError:  # duas abas ao mesmo tempo
            db.session.rollback()

    @staticmethod
    def _resgatados(student_id):
        mapa = {}
        for c in GoalClaim.query.filter_by(student_id=student_id):
            mapa.setdefault(c.goal_key, set()).add(c.tier)
        return mapa

    @staticmethod
    def listar(student_id):
        resgatados = GoalService._resgatados(student_id)
        cartoes = []
        for meta in CATALOGO:
            valor = meta.medir(student_id)
            feitos = resgatados.get(meta.key, set())
            degraus = [
                {"alvo": alvo, "pontos": pontos,
                 "resgatado": i in feitos, "atingido": valor >= alvo}
                for i, (alvo, pontos) in enumerate(meta.degraus)
            ]
            atual = next((i for i, d in enumerate(degraus) if not d["resgatado"]), None)
            completa = atual is None
            degrau = degraus[-1 if completa else atual]
            cartoes.append({
                "key": meta.key,
                "titulo": meta.titulo,
                "descricao": meta.descricao,
                "icone": meta.icone,
                "unidade": meta.unidade,
                "valor": valor,
                "alvo": degrau["alvo"],
                "pontos": degrau["pontos"],
                "nivel": len(feitos),
                "niveis": len(degraus),
                "completa": completa,
                "pronto": (not completa) and degrau["atingido"],
                "prontos": sum(1 for d in degraus if d["atingido"] and not d["resgatado"]),
                "pct": 100 if completa else min(100, round(valor / degrau["alvo"] * 100)),
                "degraus": degraus,
            })
        # prontas para resgatar primeiro, depois em andamento, concluídas no fim
        cartoes.sort(key=lambda c: (c["completa"], not c["pronto"], -c["pct"]))
        return cartoes

    @staticmethod
    def contar(student_id):
        cartoes = GoalService.listar(student_id)
        total = sum(c["niveis"] for c in cartoes)
        concluidas = sum(c["nivel"] for c in cartoes)
        return {
            "todas": total,
            "concluidas": concluidas,
            "abertas": total - concluidas,
            "prontas": sum(c["prontos"] for c in cartoes),
        }

    @staticmethod
    def resgatar(student_id, key):
        """Resgata todos os degraus já atingidos de uma meta. Devolve os pontos ganhos."""
        meta = CATALOGO_POR_CHAVE.get(key)
        if meta is None:
            raise GoalError("Meta não encontrada.")

        valor = meta.medir(student_id)
        feitos = GoalService._resgatados(student_id).get(key, set())
        total = 0
        try:
            for i, (alvo, pontos) in enumerate(meta.degraus):
                if i in feitos or valor < alvo:
                    continue
                claim = GoalClaim(student_id=student_id, goal_key=key, tier=i,
                                  points_awarded=pontos)
                db.session.add(claim)
                db.session.flush()  # gera o id, usado como ref_id (único por resgate)
                PointsService.conceder(student_id, pontos, PointTransaction.GOAL_TIER, claim.id)
                total += pontos
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise GoalError("Esta recompensa já foi resgatada.")

        if total == 0:
            raise GoalError("Esta meta ainda não atingiu o próximo degrau.")
        return total