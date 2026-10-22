from app import db
from app.models.student import Student

DOMINIOS_IF = ["@escolar.ifrn.edu.br", "@academico.ifrn.edu.br"]


class StudentService:

    @staticmethod
    def listar():
        return Student.query.all()

    @staticmethod
    def buscar_por_id(id):
        return Student.query.get(id)

    @staticmethod
    def buscar_por_email(email):
        return Student.query.filter_by(email=email).first()

    @staticmethod
    def buscar_por_matricula_suap(matricula_suap):
        return Student.query.filter_by(matricula_suap=matricula_suap).first()

    @staticmethod
    def salvar(formulario):
        """
        Cadastro manual (sem SUAP). `is_if` NUNCA vem do formulário: é
        calculado aqui, a partir do domínio do e-mail informado (Plano B).
        Isso evita que o usuário se autodeclare aluno do IF marcando um
        checkbox.
        """
        student = Student()
        formulario.populate_obj(student)
        student.is_if = StudentService._email_e_institucional(student.email)
        student.set_password(formulario.password.data)

        db.session.add(student)
        db.session.commit()
        return student

    @staticmethod
    def atualizar(student, formulario):
        formulario.populate_obj(student)
        student.is_if = StudentService._email_e_institucional(student.email)
        if formulario.password.data:
            student.set_password(formulario.password.data)

        db.session.commit()
        return student

    @staticmethod
    def remover(student):
        db.session.delete(student)
        db.session.commit()

    @staticmethod
    def criar_ou_atualizar_via_suap(dados_suap, turma_id=None):
        student = StudentService.buscar_por_matricula_suap(
            dados_suap["matricula_suap"]
        )

        if student is None:
            student = StudentService.buscar_por_email(dados_suap["email"])

        if student is None:
            student = Student()
            db.session.add(student)

        student.name = dados_suap["nome"]
        student.email = dados_suap["email"]
        student.matricula_suap = dados_suap["matricula_suap"]
        student.is_if = True
        if turma_id is not None:
            student.turma_id = turma_id

        db.session.commit()
        return student

    @staticmethod
    def _email_e_institucional(email):
        return any(email.endswith(dominio) for dominio in DOMINIOS_IF)