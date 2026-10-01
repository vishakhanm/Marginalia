from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

from app.schemas.auth import UserRegisterRequest, TokenResponse, UserInfo
from app.services import auth_service
from app.core.security import create_access_token, get_current_user
from app.core.config import get_settings

settings = get_settings()
router = APIRouter()

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@router.post("/register", response_model=UserInfo)
def register(request: UserRegisterRequest):
    """Create a new email/password account."""
    try:
        return auth_service.register_user(request.email, request.password, request.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Log in with email/password. Uses the standard OAuth2 password-flow form
    shape (username + password) so this plugs directly into Swagger UI's
    "Authorize" button — `username` here is the user's email.
    """
    try:
        return auth_service.authenticate_user(form_data.username, form_data.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserInfo)
def me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return auth_service.doc_to_user_info(current_user)


@router.get("/google/login")
async def google_login(request: Request):
    """Redirect the browser to Google's consent screen."""
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Google redirects here after consent. We exchange the code for user info,
    find-or-create a local user, issue our own JWT, and redirect back to the
    frontend with that token — from here on the app only ever deals with one
    token type, regardless of how the user signed in.
    """
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo") or await oauth.google.userinfo(token=token)

    user = auth_service.get_or_create_oauth_user(
        email=userinfo["email"], name=userinfo.get("name"), provider="google"
    )
    jwt_token = create_access_token(subject=user.id)

    return RedirectResponse(f"{settings.frontend_url}/oauth-callback?token={jwt_token}")