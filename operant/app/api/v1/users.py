from __future__ import annotations

from fastapi import APIRouter, Depends

from operant.app.api.deps import get_current_user
from operant.app.schemas.users import UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user


