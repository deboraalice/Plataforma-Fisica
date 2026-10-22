import os

from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import (
    OAuth2Error,
    AccessDeniedError,
    InvalidGrantError,
    MissingTokenError,
)

SUAP_AUTH_BASE_URL = "https://suap.ifrn.edu.br/o/authorize/"
SUAP_TOKEN_URL = "https://suap.ifrn.edu.br/o/token/"
SUAP_USER_INFO_URL = "https://suap.ifrn.edu.br/api/eu/"

SUAP_SCOPES = ["identificacao_do_usuario", "email"]


class SuapAuthError(Exception):
    pass

class AuthService:
    @staticmethod
    def _client():
        client_id = os.environ.get("SUAP_CLIENT_ID")
        client_secret = os.environ.get("SUAP_CLIENT_SECRET")
        redirect_uri = os.environ.get("SUAP_REDIRECT_URI")

        if not all([client_id, client_secret, redirect_uri]):
            raise RuntimeError(
                "SUAP_CLIENT_ID, SUAP_CLIENT_SECRET e SUAP_REDIRECT_URI "
                "precisam estar definidos como variáveis de ambiente."
            )
        return client_id, client_secret, redirect_uri

    @staticmethod
    def get_authorization_url():
        client_id, _, redirect_uri = AuthService._client()
        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=SUAP_SCOPES)
        return oauth.authorization_url(SUAP_AUTH_BASE_URL)

    @staticmethod
    def get_user_data(authorization_response_url, state):
        client_id, client_secret, redirect_uri = AuthService._client()
        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, state=state)

        try:
            oauth.fetch_token(
                SUAP_TOKEN_URL,
                authorization_response=authorization_response_url,
                client_secret=client_secret,
            )
        except AccessDeniedError:
            raise SuapAuthError(
                "Você cancelou a autorização de acesso ao SUAP. "
                "Tente novamente se quiser entrar com sua conta institucional."
            )
        except (InvalidGrantError, MissingTokenError):
            raise SuapAuthError(
                "O link de login com o SUAP expirou ou já foi utilizado. "
                "Tente entrar novamente."
            )
        except OAuth2Error as e:
            raise SuapAuthError(f"Não foi possível autenticar com o SUAP: {e}")

        try:
            response = oauth.get(SUAP_USER_INFO_URL, timeout=10)
            response.raise_for_status()
        except Exception:
            raise SuapAuthError(
                "Login no SUAP funcionou, mas não conseguimos buscar seus "
                "dados. Tente novamente em instantes."
            )

        dados = response.json()

        obrigatorios = ["identificacao", "nome_usual", "email", "tipo_vinculo"]
        faltando = [campo for campo in obrigatorios if not dados.get(campo)]
        if faltando:
            raise SuapAuthError(
                "O SUAP não retornou todos os dados necessários "
                f"({', '.join(faltando)}). Contate o suporte."
            )

        return {
            "matricula_suap": dados["identificacao"],
            "nome": dados["nome_usual"],
            "email": dados["email"],
            "tipo_vinculo": dados["tipo_vinculo"],
            "vinculo": dados.get("vinculo", {}),
        }