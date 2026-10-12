from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

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

with app.app_context():
    db.create_all()