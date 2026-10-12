from app import db
from app.models.professor import Professor


class ProfessorService:
    @staticmethod
    def listar():
        return Professor.query.all()

    @staticmethod
    def buscar_por_id(id):
        return Professor.query.get(id)

    @staticmethod
    def buscar_por_email(email):
        return Professor.query.filter_by(email=email).first()

    @staticmethod
    def buscar_por_matricula_suap(matricula_suap):
        return Professor.query.filter_by(matricula_suap=matricula_suap).first()

    @staticmethod
    def salvar(formulario):
        professor = Professor()
        formulario.populate_obj(professor)
        professor.set_password(formulario.password.data)

        db.session.add(professor)
        db.session.commit()
        return professor

    @staticmethod
    def atualizar(professor, formulario):
        formulario.populate_obj(professor)
        if formulario.password.data:
            professor.set_password(formulario.password.data)

        db.session.commit()
        return professor

    @staticmethod
    def remover(professor):
        db.session.delete(professor)
        db.session.commit()

    @staticmethod
    def criar_ou_atualizar_via_suap(dados_suap):
        professor = ProfessorService.buscar_por_matricula_suap(
            dados_suap["matricula_suap"]
        )

        if professor is None:
            professor = ProfessorService.buscar_por_email(dados_suap["email"])

        if professor is None:
            professor = Professor()
            db.session.add(professor)

        professor.name = dados_suap["nome"]
        professor.email = dados_suap["email"]
        professor.matricula_suap = dados_suap["matricula_suap"]

        db.session.commit()
        return professor