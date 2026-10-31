from functools import wraps

from flask import flash, jsonify, redirect, url_for
from flask_login import current_user

from app.models.student import Student
from app.models.professor import Professor


def _e_aluno():
    return current_user.is_authenticated and isinstance(
        current_user._get_current_object(), Student
    )


def student_required(view):
    """Páginas: exige login como aluno (as telas de estudo são do aluno)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Faça login para acessar essa página.", "warning")
            return redirect(url_for("login"))
        if not _e_aluno():
            flash("Esta área é exclusiva para alunos.", "warning")
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapper


def api_student_required(view):
    """Rotas JSON (AJAX): respondem com erro em JSON em vez de redirecionar."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(ok=False, error="Sessão expirada. Faça login novamente."), 401
        if not _e_aluno():
            return jsonify(ok=False, error="Recurso exclusivo para alunos."), 403
        return view(*args, **kwargs)

    return wrapper


def professor_required(view):
    """Páginas: exige login como professor."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Faça login para acessar essa página.", "warning")
            return redirect(url_for("login"))
        if not isinstance(current_user._get_current_object(), Professor):
            flash("Esta área é exclusiva para professores.", "warning")
            return redirect(url_for("index"))
        return view(*args, **kwargs)

    return wrapper


def api_professor_required(view):
    """Rotas JSON: responde com erro em JSON para usuários sem perfil docente."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify(ok=False, error="Sessão expirada. Faça login novamente."), 401
        if not isinstance(current_user._get_current_object(), Professor):
            return jsonify(ok=False, error="Recurso exclusivo para professores."), 403
        return view(*args, **kwargs)

    return wrapper
