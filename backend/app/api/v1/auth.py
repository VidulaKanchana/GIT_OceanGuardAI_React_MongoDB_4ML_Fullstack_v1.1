import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.db.connection import get_database
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import UserCreate, UserLogin, Token, TokenRefreshRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials.")

    db = get_database()
    user = db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate):
    db = get_database()
    existing = db.users.find_one({"email": user_in.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

    user_id = f"U{uuid.uuid4().hex[:6].upper()}"
    user_doc = {
        "user_id": user_id,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "hashed_password": get_password_hash(user_in.password),
        "role": user_in.role if user_in.role in ("fisherman", "researcher", "admin") else "fisherman",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    db.users.insert_one(user_doc)
    return user_doc

@router.post("/login", response_model=Token)
def login(login_in: UserLogin):
    db = get_database()
    user = db.users.find_one({"email": login_in.email})
    if not user or not verify_password(login_in.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    access_token = create_access_token(user["user_id"], role=user.get("role", "fisherman"))
    refresh_token = create_refresh_token(user["user_id"], role=user.get("role", "fisherman"))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.get("role", "fisherman"),
        "full_name": user.get("full_name", "User"),
        "user_id": user["user_id"]
    }

@router.post("/refresh", response_model=Token)
def refresh(refresh_in: TokenRefreshRequest):
    try:
        payload = decode_token(refresh_in.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token type.")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    db = get_database()
    user = db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    access_token = create_access_token(user["user_id"], role=user.get("role", "fisherman"))
    new_refresh = create_refresh_token(user["user_id"], role=user.get("role", "fisherman"))

    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "role": user.get("role", "fisherman"),
        "full_name": user.get("full_name", "User"),
        "user_id": user["user_id"]
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
