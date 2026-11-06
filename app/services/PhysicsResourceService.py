import re
from urllib.parse import parse_qs, urlparse

from app import db
from app.models.physics import PhysicsResource, PhysicsTopic
from app.timeutils import agora_utc


YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"youtube.com", "m.youtube.com", "youtube-nocookie.com"}


class ResourceError(ValueError):
    pass


def _youtube_video_id(url):
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if host == "youtu.be":
        candidate = path_parts[0] if path_parts else ""
    elif host in YOUTUBE_HOSTS or host == "www.youtube.com" or host == "www.youtube-nocookie.com":
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [""])[0]
        elif len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts", "live"}:
            candidate = path_parts[1]
        else:
            candidate = ""
    else:
        return None

    if not YOUTUBE_ID.fullmatch(candidate):
        raise ResourceError("Não consegui identificar um vídeo válido neste link do YouTube.")
    return candidate


def _validar_url(url):
    value = (url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ResourceError("Informe um link iniciado por http:// ou https://.")
    if parsed.username or parsed.password:
        raise ResourceError("Links com credenciais embutidas não são aceitos.")
    return value, _youtube_video_id(value)


class PhysicsResourceService:
    @staticmethod
    def recursos_publicos(topic_id):
        return (
            PhysicsResource.query.filter_by(
                topic_id=topic_id,
                is_active=True,
            )
            .order_by(PhysicsResource.created_at, PhysicsResource.id)
            .all()
        )

    @staticmethod
    def listar_para_gerencia(topic_id):
        return (
            PhysicsResource.query.filter_by(topic_id=topic_id)
            .order_by(PhysicsResource.created_at.desc(), PhysicsResource.id.desc())
            .all()
        )

    @staticmethod
    def buscar_para_gerencia(resource_id, topic_id):
        return PhysicsResource.query.filter_by(
            id=resource_id,
            topic_id=topic_id,
        ).first()

    @staticmethod
    def salvar_publico(topic_id, title, description, url, resource=None):
        if PhysicsTopic.query.filter_by(id=topic_id).first() is None:
            raise ResourceError("O tópico selecionado não existe.")

        normalized_url, youtube_id = _validar_url(url)
        material = resource or PhysicsResource()
        if resource is not None and resource.topic_id != topic_id:
            raise ResourceError("Este material pertence a outro tópico.")

        material.topic_id = topic_id
        material.team_id = None
        material.professor_id = None
        material.title = title.strip()
        material.description = (description or "").strip() or None
        material.url = normalized_url
        material.youtube_video_id = youtube_id
        material.updated_at = agora_utc()
        material.is_active = True
        db.session.add(material)
        db.session.commit()
        return material

    @staticmethod
    def remover_material(material):
        material.is_active = False
        material.updated_at = agora_utc()
        db.session.commit()
