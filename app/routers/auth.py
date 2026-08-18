from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
router = APIRouter(tags=["Auth"])

# Ключи доступа
CAPTAIN_PINS = ["086", "aivar", "aivar086", "1986"]
GUEST_PINS = ["777", "camp777", "рыбалка", "друзья", "guest"]

COOKIE_AUTH_ROLE = "aivar_camp_role"
ROLE_CAPTAIN = "captain"
ROLE_GUEST = "guest"

def get_user_role(request: Request) -> str:
    """Возвращает роль пользователя: 'captain', 'guest' или 'none'."""
    # Проверка ссылки с ключом ?key=...
    key_param = request.query_params.get("key")
    if key_param:
        clean_k = key_param.strip().lower()
        if clean_k in [p.lower() for p in CAPTAIN_PINS]:
            return ROLE_CAPTAIN
        if clean_k in [p.lower() for p in GUEST_PINS]:
            return ROLE_GUEST
            
    role = request.cookies.get(COOKIE_AUTH_ROLE)
    if role in [ROLE_CAPTAIN, ROLE_GUEST]:
        return role
    return "none"

def is_captain(request: Request) -> bool:
    return get_user_role(request) == ROLE_CAPTAIN

def is_authorized(request: Request) -> bool:
    return get_user_role(request) in [ROLE_CAPTAIN, ROLE_GUEST]

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error, "redirect_url": request.query_params.get("redirect_url", "/")}
    )

@router.post("/auth/login")
def login(request: Request, response: Response, pin: str = Form(...), redirect_url: str = Form("/")):
    clean_pin = pin.strip().lower()
    
    # 1. Проверка на Капитана (Айвар)
    if clean_pin in [p.lower() for p in CAPTAIN_PINS]:
        redir = RedirectResponse(url=redirect_url or "/", status_code=303)
        redir.set_cookie(
            key=COOKIE_AUTH_ROLE,
            value=ROLE_CAPTAIN,
            max_age=60 * 60 * 24 * 90, # 90 дней
            httponly=True,
            samesite="lax"
        )
        return redir
        
    # 2. Проверка на Гостя (Друзья)
    if clean_pin in [p.lower() for p in GUEST_PINS]:
        redir = RedirectResponse(url=redirect_url or "/", status_code=303)
        redir.set_cookie(
            key=COOKIE_AUTH_ROLE,
            value=ROLE_GUEST,
            max_age=60 * 60 * 24 * 90, # 90 дней
            httponly=True,
            samesite="lax"
        )
        return redir

    # Неверный PIN
    return RedirectResponse(url=f"/login?error=1&redirect_url={redirect_url}", status_code=303)

@router.post("/auth/logout")
def logout(redirect_url: str = Form("/login")):
    redir = RedirectResponse(url="/login", status_code=303)
    redir.delete_cookie(key=COOKIE_AUTH_ROLE)
    return redir
