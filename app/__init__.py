import sys

from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy import inspect, text
from config import Config
from flask_migrate import Migrate


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
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
from app.services.RankingService import RankingService
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


def _upgrade_physics_resource_file_schema():
    """Adiciona campos opcionais para arquivos anexados aos materiais."""
    inspector = inspect(db.engine)
    if "physics_resource" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("physics_resource")
    }
    dialect = db.engine.dialect.name
    binary_type = "BYTEA" if dialect == "postgresql" else (
        "LONGBLOB" if dialect == "mysql" else "BLOB"
    )
    additions = {
        "file_data": f"{binary_type} NULL",
        "file_mime_type": "VARCHAR(100) NULL",
    }
    for name, definition in additions.items():
        if name not in columns:
            db.session.execute(
                text(f"ALTER TABLE physics_resource ADD COLUMN {name} {definition}")
            )
    db.session.commit()


def _upgrade_quiz_image_schema():
    """Adiciona campos de imagem a questões e alternativas já existentes."""
    inspector = inspect(db.engine)
    for table_name in ("quiz_question", "quiz_option"):
        if table_name not in inspector.get_table_names():
            continue
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "image_filename" not in columns:
            db.session.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN image_filename VARCHAR(255) NULL")
            )
    db.session.commit()

_is_flask_db_command = "db" in sys.argv[1:]


def _upgrade_video_watch_schema():
    """Atualiza registros de acompanhamento de vídeo já existentes."""
    inspector = inspect(db.engine)
    if "video_watch" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("video_watch")}
    if "duration" not in columns:
        db.session.execute(
            text("ALTER TABLE video_watch ADD COLUMN duration FLOAT NOT NULL DEFAULT 0")
        )
    if "youtube_video_id" not in columns:
        db.session.execute(
            text("ALTER TABLE video_watch ADD COLUMN youtube_video_id VARCHAR(11) NULL")
        )

    # Associa as linhas antigas ao ID real do vídeo sem descartar o progresso.
    db.session.execute(text(
        "UPDATE video_watch SET youtube_video_id = "
        "(SELECT physics_resource.youtube_video_id FROM physics_resource "
        "WHERE physics_resource.id = video_watch.resource_id) "
        "WHERE youtube_video_id IS NULL"
    ))

    # Dados antigos podem ter o mesmo vídeo cadastrado em mais de um material.
    # Preserva o registro mais avançado e deixa os duplicados históricos sem chave.
    db.session.execute(text(
        "WITH ranked AS ("
        " SELECT id, ROW_NUMBER() OVER ("
        "  PARTITION BY student_id, youtube_video_id "
        "  ORDER BY (completed_at IS NOT NULL) DESC, watched_seconds DESC, id ASC"
        " ) AS rn FROM video_watch WHERE youtube_video_id IS NOT NULL"
        ") UPDATE video_watch SET youtube_video_id = NULL "
        "WHERE id IN (SELECT id FROM ranked WHERE rn > 1)"
    ))
    db.session.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_video_watch_student_youtube_video "
        "ON video_watch (student_id, youtube_video_id)"
    ))
    db.session.commit()


def _backfill_quiz_completions():
    """Trata simulados já enviados como concluídos no novo fluxo de tentativa única."""
    if "quiz_completion" not in inspect(db.engine).get_table_names():
        return
    db.session.execute(text(
        "INSERT INTO quiz_completion (student_id, quiz_id, attempt_id, completed_at, points_awarded) "
        "SELECT attempt.student_id, attempt.quiz_id, attempt.id, attempt.completed_at, 0 "
        "FROM quiz_attempt AS attempt "
        "WHERE attempt.completed_at IS NOT NULL "
        "AND attempt.id = (SELECT MIN(previous.id) FROM quiz_attempt AS previous "
        " WHERE previous.student_id = attempt.student_id "
        " AND previous.quiz_id = attempt.quiz_id AND previous.completed_at IS NOT NULL) "
        "AND NOT EXISTS (SELECT 1 FROM quiz_completion AS completion "
        " WHERE completion.student_id = attempt.student_id AND completion.quiz_id = attempt.quiz_id)"
    ))
    db.session.commit()


if not _is_flask_db_command:
    with app.app_context():
        db.create_all()
        _upgrade_physics_topic_schema()
        _upgrade_physics_resource_file_schema()
        _upgrade_quiz_image_schema()
        _upgrade_video_watch_schema()
        _backfill_quiz_completions()
        RankingService.registrar_pontos_historicos()
        PhysicsService.seed_conteudo_inicial()
