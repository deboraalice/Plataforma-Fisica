import re
from urllib.parse import parse_qs, urlparse

from app import db
from app.models.physics import PhysicsResource, PhysicsTopic
from app.timeutils import agora_utc
from sqlalchemy.orm import defer


YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"youtube.com", "m.youtube.com", "youtube-nocookie.com"}


class ResourceError(ValueError):
    pass


MAX_RESOURCE_FILE_BYTES = 3 * 1024 * 1024


def _ler_arquivo(upload):
    data = upload.stream.read(MAX_RESOURCE_FILE_BYTES + 1)
    if len(data) > MAX_RESOURCE_FILE_BYTES:
        raise ResourceError("O arquivo deve ter no máximo 3 MB.")

    if data.startswith(b"%PDF-"):
        mime_type = "application/pdf"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime_type = "image/png"
    elif data.startswith(b"\xff\xd8\xff"):
        mime_type = "image/jpeg"
    elif data.startswith((b"GIF87a", b"GIF89a")):
        mime_type = "image/gif"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        mime_type = "image/webp"
    else:
        raise ResourceError("Envie um PDF ou uma imagem PNG, JPG, GIF ou WEBP válida.")

    return data, mime_type


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
            .options(defer(PhysicsResource.file_data))
            .order_by(PhysicsResource.created_at, PhysicsResource.id)
            .all()
        )

    @staticmethod
    def listar_para_gerencia(topic_id):
        return (
            PhysicsResource.query.filter_by(topic_id=topic_id)
            .options(defer(PhysicsResource.file_data))
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
    def salvar_publico(topic_id, title, description, url, arquivo=None, resource=None):
        if PhysicsTopic.query.filter_by(id=topic_id).first() is None:
            raise ResourceError("O tópico selecionado não existe.")

        url_value = (url or "").strip()
        upload_enviado = arquivo is not None and bool(arquivo.filename)
        novo_arquivo = None

        if upload_enviado:
            if url_value and (resource is None or url_value != (resource.url or "")):
                raise ResourceError("Escolha um link ou um arquivo por vez.")
            novo_arquivo = _ler_arquivo(arquivo)
            normalized_url, youtube_id = "", None
        elif url_value:
            normalized_url, youtube_id = _validar_url(url_value)
        elif resource is not None and resource.file_mime_type:
            normalized_url, youtube_id = "", None
        else:
            raise ResourceError("Informe um link ou envie um arquivo.")

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
        if novo_arquivo is not None:
            material.file_data, material.file_mime_type = novo_arquivo
        elif url_value:
            material.file_data = None
            material.file_mime_type = None
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
