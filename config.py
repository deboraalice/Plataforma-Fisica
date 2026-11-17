import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

basedir = os.path.abspath(os.path.dirname(__file__))

_env_path = os.path.join(basedir, ".env")
_env_loaded = load_dotenv(_env_path, override=True)

CURRENT_DATABASE = (os.getenv("CURRENT_DATABASE") or "sqlite").strip().lower()
DB_USERNAME = (os.getenv("DB_USERNAME") or "").strip()
DB_PASSWORD = os.getenv("DB_PASSWORD") or ""
DB_HOST = (os.getenv("DB_HOST") or "").strip()
DB_PORT = (os.getenv("DB_PORT") or "").strip()
DB_NAME = (os.getenv("DB_NAME") or "").strip()
SQLITE_DATABASE_PATH = os.path.join(basedir, "app.db")

if CURRENT_DATABASE in ("postgresql", "mysql"):
    _missing = [
        nome
        for nome, valor in {
            "DB_USERNAME": DB_USERNAME,
            "DB_PASSWORD": DB_PASSWORD,
            "DB_HOST": DB_HOST,
            "DB_PORT": DB_PORT,
            "DB_NAME": DB_NAME,
        }.items()
        if not valor
    ]
    if _missing:
        raise RuntimeError(
            f"CURRENT_DATABASE={CURRENT_DATABASE}, mas faltam variáveis: {', '.join(_missing)}. "
            f"(.env em {_env_path} carregado: {_env_loaded})"
        )


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    if CURRENT_DATABASE == "sqlite":
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{SQLITE_DATABASE_PATH}"
    elif CURRENT_DATABASE == "mysql":
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+mysqlconnector://{DB_USERNAME}:{quote_plus(DB_PASSWORD)}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
    elif CURRENT_DATABASE == "postgresql":
        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{DB_USERNAME}:{quote_plus(DB_PASSWORD)}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )
   
        SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}
    else:
        raise RuntimeError(
            f"CURRENT_DATABASE inválido: '{CURRENT_DATABASE}'. Use sqlite, mysql ou postgresql."
        )