import json
import logging
import socket
from typing import Dict

import jwt
import requests
import uvicorn
from fastapi import FastAPI, Header, Form
from keycloak import KeycloakAdmin, KeycloakOpenID
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.responses import RedirectResponse

LOCAL_IP = socket.gethostbyname(socket.gethostname())

APP_BASE_URL = f"http://{LOCAL_IP}:3000/"
KEYCLOAK_BASE_URL = f"http://{LOCAL_IP}:8180"
AUTH_URL = (
    f"{KEYCLOAK_BASE_URL}/auth/realms/test/protocol/openid-connect/auth?client_id=kong&response_type=code&redirect_uri=http://localhost:8000/users/auth"
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
@app.post("/users/register")
async def create_user(email: str = Form(...), username: str = Form(...), password: str = Form(...), firstName: str = Form(None), lastName: str = Form(None), referral: str = Form(None)):
    new_user = keycloak_admin.create_user({"email": email,
                    "username": username,
                    "enabled": True,
                    "firstName": firstName or "",
                    "lastName": lastName or "",
                    "attributes": {"referral": referral or ""},
                    "credentials": [{"value": password,"type": "password",}]})
    return {"created_user_id": new_user}

# Logout
@app.get("/users/logout")
def logout(request: Request,):
    refresh_token: str = request.cookies.get("Refresh")
    if refresh_token == None:
        return {"message": "Not logged in."}
    keycloak_openid.logout(refresh_token)
    response = RedirectResponse(url="http://localhost:8000/")
    response.delete_cookie("Authorization", domain="localhost")
    response.delete_cookie("Refresh", domain="localhost")
    return response

# Refresh token, not used
@app.get("/users/refresh")
def refresh_token(request: Request,):
    refresh_token: str = request.cookies.get("Refresh")
    if refresh_token == None:
        return {"message": "No refresh token."}
    token = keycloak_openid.refresh_token(refresh_token)

    access_token = token["access_token"]
    refresh_token = token["refresh_token"]

    response = RedirectResponse(url="/")
    response.set_cookie("Authorization", value=f"{access_token}")
    response.set_cookie("Refresh", value=f"{refresh_token}")
    return response

# Introspect Token, not used
@app.get("/users/introspect")
def introspect_token(Authorization: str = Header(None)):
    if Authorization == None:
        return {"message": "Token not provided."}
    token_info = keycloak_openid.introspect(Authorization[7:])
    return {"token_info": token_info}

# Login
@app.get("/users/login")
async def login() -> RedirectResponse:
    return RedirectResponse(AUTH_URL)

# Get authorization_code and set cookies after successful login
@app.get("/users/auth")
async def auth(code: str) -> RedirectResponse:
    payload = (
        f"grant_type=authorization_code&code={code}"
        f"&redirect_uri=http://localhost:8000/users/auth&client_id=kong&client_secret=4cd2e98f-df15-4972-84c8-1be974e9aba6"
    )
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.request(
        "POST", TOKEN_URL, data=payload, headers=headers
    )
    
    token_body = json.loads(token_response.content)
    access_token = token_body["access_token"]
    refresh_token = token_body["refresh_token"]

    response = RedirectResponse(url="/")
    response.set_cookie("Authorization", value=f"{access_token}")
    response.set_cookie("Refresh", value=f"{refresh_token}")
    return response

# Starting page, token decode
@app.get("/")
async def root(Authorization: str = Header(None)) -> Dict:
    scheme, credentials = get_authorization_scheme_param(Authorization)
    if credentials:
        public_key = "b'-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs2iY+UNfz035EspzTZUeSai+FbBQC487BLsWC/BA+d5b1UFVs0k1erXnqrFBWjKzgn10r3fMfPlPn8ffK8iEuvBEoJ5vnRaHRqjhIi1DZ+h1o5sC9qhty0p5k+Nu9i0rV/CpY6PkAQw/e7kXBMWhK8zM/TAsA0GQUOaZDm/4WeNUq2roMAX+fAJZfMFiI2/WRvBQKcTY1SB6wJhC9c5QhBgWs83XR9EGP6BxyzvJMroR0kMyb+B7ITWbzpKXuUWbhsxRWm0Mz2nwHo9jsREC03wN0CnD+vocCnKjLv/4Bqy9igwKBT2bpAssR0Y7p3v1QZmSO3D4OxUhhkoWBZBCyQIDAQAB'"

        decoded = jwt.decode(
            credentials, key=public_key, verify=False
        )
        return {"message": "You're logged in!", "decoded_token": decoded}
    else:
        return {"message": "You're not logged in!"}