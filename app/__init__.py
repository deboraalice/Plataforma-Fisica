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
from app.simulators import simulators


app.register_blueprint(simulators)

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
    _upgrade_physics_topic_schema()
    PhysicsService.seed_conteudo_inicial()
