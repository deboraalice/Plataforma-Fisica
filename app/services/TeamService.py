import secrets
import string

from app import db
from app.models.team import Team, TeamMembership
from app.timeutils import agora_utc


class TeamService:
    CODE_LENGTH = 6
    CODE_ALPHABET = string.ascii_uppercase + string.digits

    @staticmethod
    def _novo_codigo():
        for _ in range(20):
            code = "".join(
                secrets.choice(TeamService.CODE_ALPHABET)
                for _ in range(TeamService.CODE_LENGTH)
            )
            if Team.query.filter_by(access_code=code).first() is None:
                return code
        raise RuntimeError("Não foi possível gerar um código de turma único.")

    @staticmethod
    def listar_do_professor(professor_id):
        return (
            Team.query.filter_by(professor_id=professor_id)
            .order_by(Team.archived_at.is_(None).desc(), Team.id.desc())
            .all()
        )

    @staticmethod
    def buscar_do_professor(team_id, professor_id):
        return Team.query.filter_by(
            id=team_id,
            professor_id=professor_id,
        ).first()

    @staticmethod
    def criar(professor_id, nome):
        team = Team(
            nome=nome.strip(),
            professor_id=professor_id,
            access_code=TeamService._novo_codigo(),
            access_code_active=True,
        )
        db.session.add(team)
        db.session.commit()
        return team

    @staticmethod
    def renomear(team, nome):
        team.nome = nome.strip()
        db.session.commit()
        return team

    @staticmethod
    def renovar_codigo(team):
        if team.archived_at is not None:
            raise ValueError("Turmas arquivadas não podem receber novos códigos.")
        team.access_code = TeamService._novo_codigo()
        team.access_code_active = True
        db.session.commit()
        return team.access_code

    @staticmethod
    def desativar_codigo(team):
        team.access_code_active = False
        db.session.commit()

    @staticmethod
    def buscar_por_codigo(code):
        return Team.query.filter_by(
            access_code=code.strip().upper(),
            access_code_active=True,
            archived_at=None,
        ).first()

    @staticmethod
    def entrar(student, team):
        if team.archived_at is not None or not team.access_code_active:
            raise ValueError("O código desta turma não está mais ativo.")
        if student.team_id is not None:
            raise ValueError("Saia da turma atual antes de entrar em outra.")

        membership = TeamMembership(
            student_id=student.id,
            team_id=team.id,
            joined_at=agora_utc(),
        )
        db.session.add(membership)
        student.team_id = team.id
        db.session.commit()
        return membership

    @staticmethod
    def _encerrar_vinculo(student, team_id):
        membership = (
            TeamMembership.query.filter_by(
                student_id=student.id,
                team_id=team_id,
                left_at=None,
            )
            .order_by(TeamMembership.id.desc())
            .first()
        )
        agora = agora_utc()
        if membership is None:
            # Vínculo legado: sabe-se que estava ativo, mas não quando começou.
            membership = TeamMembership(
                student_id=student.id,
                team_id=team_id,
                joined_at=None,
                left_at=agora,
            )
            db.session.add(membership)
        else:
            membership.left_at = agora

    @staticmethod
    def sair(student):
        if student.team_id is None:
            return False
        team_id = student.team_id
        TeamService._encerrar_vinculo(student, team_id)
        student.team_id = None
        db.session.commit()
        return True

    @staticmethod
    def remover_aluno(team, student):
        if student.team_id != team.id:
            return False
        TeamService._encerrar_vinculo(student, team.id)
        student.team_id = None
        db.session.commit()
        return True

    @staticmethod
    def arquivar(team):
        if team.archived_at is not None:
            return False
        team.archived_at = agora_utc()
        team.access_code_active = False
        for student in team.students.all():
            TeamService._encerrar_vinculo(student, team.id)
            student.team_id = None
        db.session.commit()
        return True

    @staticmethod
    def historico_do_aluno(student_id, limit=20):
        return (
            TeamMembership.query.filter_by(student_id=student_id)
            .order_by(TeamMembership.id.desc())
            .limit(limit)
            .all()
        )
