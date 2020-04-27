import json
import logging
import socket
from typing import Dict

import jwt
import requests
import uvicorn
from fastapi import FastAPI, Header
from keycloak import KeycloakAdmin, KeycloakOpenID
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.responses import RedirectResponse

LOCAL_IP = socket.gethostbyname(socket.gethostname())

APP_BASE_URL = f"http://{LOCAL_IP}:3000/"
KEYCLOAK_BASE_URL = f"http://{LOCAL_IP}:8180"
AUTH_URL = (
    f"{KEYCLOAK_BASE_URL}/auth/realms/test/protocol/openid-connect/auth?client_id=kong&response_type=code"
)
TOKEN_URL = (
    f"{KEYCLOAK_BASE_URL}/auth/realms/test/protocol/openid-connect/token"
)

logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")

app = FastAPI()


# Configure admin
keycloak_admin = KeycloakAdmin(server_url=f"http://{LOCAL_IP}:8180/auth/",
                               username='admin',
                               password='secret',
                               realm_name="test",
                               verify=False)

# Configure client
keycloak_openid = KeycloakOpenID(server_url=f"http://{LOCAL_IP}:8180/auth/",
                    client_id="kong",
                    realm_name="test",
                    client_secret_key="4cd2e98f-df15-4972-84c8-1be974e9aba6")

# Add user and set password
@app.post("/users/create")
async def create_user():
    new_user = keycloak_admin.create_user({"email": "example@example.com",
                    "username": "example@example.com",
                    "enabled": True,
                    "firstName": "Example",
                    "lastName": "Example",
                    "credentials": [{"value": "secret","type": "password",}]})
    return {"user_created": new_user}

# Get Token
@app.get("/users/token")
def get_token(user: str, password: str):
    token = keycloak_openid.token(user, password)
    return {"token": token}

# Get Userinfo
@app.get("/users")
def get_user_info(request: Request,):
    #userinfo = keycloak_openid.userinfo(token['access_token'])
    authorization: str = request.cookies.get("Authorization")
    logger.debug(authorization)
    userinfo = keycloak_openid.userinfo(authorization[7:])
    return {"userinfo": userinfo}

# Refresh token
@app.get("/users/refresh")
def refresh_token(x_refresh_token: str = Header(None)):
    token = keycloak_openid.refresh_token(x_refresh_token)
    return {"token": token}

# Logout
@app.get("/users/logout")
def logout(x_refresh_token: str = Header(None)):
    keycloak_openid.logout(x_refresh_token)

# Decode Token
@app.get("/users/decode")
def get_decoded_token(x_access_token: str = Header(None)):
    KEYCLOAK_PUBLIC_KEY = keycloak_openid.public_key()
    options = {"verify_signature": True, "verify_aud": True, "exp": True}
    token_info = keycloak_openid.decode_token(x_access_token, key=KEYCLOAK_PUBLIC_KEY, options=options)
    return {"token_info": token_info}

# Introspect Token
@app.get("/users/introspect")
def introspect_token(x_access_token: str = Header(None)):
    token_info = keycloak_openid.introspect(x_access_token)
    return {"token_info": token_info}


@app.get("/login")
async def login() -> RedirectResponse:
    return RedirectResponse(AUTH_URL)


@app.get("/auth")
async def auth(code: str) -> RedirectResponse:
    payload = (
        f"grant_type=authorization_code&code={code}"
        f"&redirect_uri={APP_BASE_URL}&client_id=kong&client_secret=4cd2e98f-df15-4972-84c8-1be974e9aba6"
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.request(
        "POST", TOKEN_URL, data=payload, headers=headers
    )

    token_body = json.loads(token_response.content)
    access_token = token_body["access_token"]
    refresh_token = token_body["refresh_token"]

    response = RedirectResponse(url="/")
    response.set_cookie("Authorization", value=f"Bearer {access_token}")
    response.set_cookie("Refresh", value=f"{refresh_token}")
    return response


@app.get("/")
async def root(request: Request,) -> Dict:
    authorization: str = request.cookies.get("Authorization")
    scheme, credentials = get_authorization_scheme_param(authorization)
    
    public_key = "b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs2iY+UNfz035EspzTZUeSai+FbBQC487BLsWC/BA+d5b1UFVs0k1erXnqrFBWjKzgn10r3fMfPlPn8ffK8iEuvBEoJ5vnRaHRqjhIi1DZ+h1o5sC9qhty0p5k+Nu9i0rV/CpY6PkAQw/e7kXBMWhK8zM/TAsA0GQUOaZDm/4WeNUq2roMAX+fAJZfMFiI2/WRvBQKcTY1SB6wJhC9c5QhBgWs83XR9EGP6BxyzvJMroR0kMyb+B7ITWbzpKXuUWbhsxRWm0Mz2nwHo9jsREC03wN0CnD+vocCnKjLv/4Bqy9igwKBT2bpAssR0Y7p3v1QZmSO3D4OxUhhkoWBZBCyQIDAQAB'"

    decoded = jwt.decode(
        credentials, key=public_key, verify=False
    )  # TODO input keycloak public key as key, disable option to verify aud
    logger.debug(decoded)

    return {"message": "You're logged in!"}