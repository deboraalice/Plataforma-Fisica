import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SUAP_URL = os.environ.get("SUAP_URL", "https://suap.ifrn.edu.br").rstrip("/")
SUAP_AUTH_URL = f"{SUAP_URL}/o/authorize/"
SUAP_TOKEN_URL = f"{SUAP_URL}/o/token/"
SUAP_USER_INFO_URL = f"{SUAP_URL}/api/rh/meus-dados/"


class SuapAuthError(Exception):
    pass


class AuthService:
    @staticmethod
    def _credentials():
        client_id = os.environ.get("SUAP_CLIENT_ID")
        client_secret = os.environ.get("SUAP_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError(
                "SUAP_CLIENT_ID e SUAP_CLIENT_SECRET precisam estar definidos "
                "como variáveis de ambiente."
            )
        return client_id, client_secret

    @staticmethod
    def get_authorization_url(redirect_uri, state):
        client_id, _ = AuthService._credentials()
        params = urlencode({
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        })
        return f"{SUAP_AUTH_URL}?{params}"

    @staticmethod
    def get_user_data(code, redirect_uri):
        client_id, client_secret = AuthService._credentials()
        token_body = urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }).encode("utf-8")
        try:
            with urlopen(Request(
                SUAP_TOKEN_URL,
                data=token_body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ), timeout=10) as response:
                token_data = json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as erro:
            raise SuapAuthError(
                "Não foi possível obter o token do SUAP. Tente novamente."
            ) from erro

        if not isinstance(token_data, dict):
            raise SuapAuthError("O SUAP retornou uma resposta de token inválida.")
        access_token = token_data.get("access_token")
        if not access_token:
            raise SuapAuthError("O SUAP não retornou um token de acesso válido.")

        try:
            with urlopen(Request(
                SUAP_USER_INFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            ), timeout=10) as response:
                dados = json.load(response)
        except (HTTPError, URLError, TimeoutError, ValueError) as erro:
            raise SuapAuthError(
                "O login no SUAP foi autorizado, mas não foi possível consultar "
                "seus dados. Tente novamente."
            ) from erro

        if not isinstance(dados, dict):
            raise SuapAuthError("O SUAP retornou um perfil em formato inesperado.")

        nome = dados.get("nome_usual") or dados.get("nome")
        email = dados.get("email")
        identificador = (
            dados.get("matricula")
            or dados.get("identificacao")
            or dados.get("username")
        )
        obrigatorios = {
            "nome": nome,
            "email": email if isinstance(email, str) else None,
            "tipo_vinculo": dados.get("tipo_vinculo"),
        }
        faltando = [campo for campo, valor in obrigatorios.items() if not valor]
        if faltando:
            raise SuapAuthError(
                "O SUAP não retornou todos os dados necessários "
                f"({', '.join(faltando)}). Contate o suporte."
            )

        return {
            "matricula_suap": str(identificador) if identificador else None,
            "nome": nome,
            "email": email.strip().lower(),
            "tipo_vinculo": dados["tipo_vinculo"],
            "vinculo": dados.get("vinculo", {}),
        }
