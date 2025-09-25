from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login")
def login():
    # Stub for initial scaffold
    return {"access_token": "stub", "token_type": "bearer"}
