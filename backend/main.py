from fastapi import APIRouter, Depends, HTTPException, Response, status
#from sqlalchemy.ext.asyncio import AsyncSession
#from sqlalchemy import select
#from ..schemas import UserCreate, UserOut, TokenPair
#from ..models import User
#from ..db import get_session
#from ..security import hash_password, verify_password, create_token, COOKIE_NAME
#from ..config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(payload: UserCreate, session: AsyncSession = Depends(get_session)):
    exists = await session.execute(select(User).where(User.email == payload.email))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password), full_name=payload.full_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
async def login(resp: Response, payload: UserCreate, session: AsyncSession = Depends(get_session)):
    q = await session.execute(select(User).where(User.email == payload.email))
    user = q.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_token(sub=user.email, minutes=settings.access_token_expire_min)
    refresh = create_token(sub=user.email, minutes=settings.refresh_token_expire_min)
    # httpOnly cookie for convenience
    resp.set_cookie(
    key=COOKIE_NAME,
    value=access,
    max_age=settings.access_token_expire_min*60,
    secure=settings.cookie_secure,
    httponly=True,
    samesite="lax",
    domain=settings.cookie_domain,
    )
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/logout")
async def logout(resp: Response):
    resp.delete_cookie(COOKIE_NAME)
    return {"ok": True}