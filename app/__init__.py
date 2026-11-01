from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import inspect, text

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = "login" 
login_manager.login_message = "Faça login para acessar essa página."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(id_composto):
    from app.services.StudentService import StudentService
    from app.services.ProfessorService import ProfessorService
    
    try:
        tipo, id_puro = id_composto.split(":", 1)
    except ValueError:
        return None
    
    if tipo == "student":
        return StudentService.buscar_por_id(int(id_puro))
    if tipo == "professor":
        return ProfessorService.buscar_por_id(int(id_puro))
    return None

from app import routes, models
from app.services.PhysicsService import PhysicsService


def _upgrade_team_schema():
    """Adiciona campos novos de turma sem exigir apagar o banco existente."""
    inspector = inspect(db.engine)
    if "team" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("team")}
    additions = {
        "access_code": "VARCHAR(6) NULL",
        "access_code_active": "BOOLEAN NOT NULL DEFAULT 1",
        "archived_at": "DATETIME NULL",
    }
    for name, definition in additions.items():
        if name not in columns:
            db.session.execute(text(f"ALTER TABLE team ADD COLUMN {name} {definition}"))

    index_names = {index["name"] for index in inspector.get_indexes("team")}
    if "ix_team_access_code" not in index_names:
        db.session.execute(
            text("CREATE UNIQUE INDEX ix_team_access_code ON team (access_code)")
        )

    # Alunos que já tinham turma antes do histórico recebem um vínculo ativo
    # com data desconhecida, em vez de uma data de entrada inventada.
    students_with_team = models.Student.query.filter(models.Student.team_id.isnot(None)).all()
    for student in students_with_team:
        active_membership = models.TeamMembership.query.filter_by(
            student_id=student.id,
            team_id=student.team_id,
            left_at=None,
        ).first()
        if active_membership is None:
            db.session.add(
                models.TeamMembership(
                    student_id=student.id,
                    team_id=student.team_id,
                    joined_at=None,
                )
            )
    db.session.commit()


def _upgrade_physics_topic_schema():
    """Acrescenta campos de apresentação aos tópicos já existentes."""
    inspector = inspect(db.engine)
    if "physics_topic" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("physics_topic")}
    additions = {
        "emoji": "VARCHAR(16) NULL",
        "summary": "TEXT NULL",
        "solved_example": "TEXT NULL",
        "simulator_url": "VARCHAR(255) NULL",
    }
    for name, definition in additions.items():
        if name not in columns:
            db.session.execute(
                text(f"ALTER TABLE physics_topic ADD COLUMN {name} {definition}")
            )
    db.session.commit()


with app.app_context():
    db.create_all()
    _upgrade_team_schema()
    _upgrade_physics_topic_schema()
    PhysicsService.seed_conteudo_inicial()
