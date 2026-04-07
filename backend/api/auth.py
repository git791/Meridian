from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from core.config import settings

# 1. Define the User model (so 'User' isn't undefined)
class User(BaseModel):
    email: str
    is_active: bool = True

# 2. Define the OAuth2 scheme (so 'oauth2_scheme' isn't undefined)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

# 3. The main Auth logic
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # If we are in demo mode, just let them in!
    if settings.DEMO_MODE:
        return User(email="demo@example.com")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # In a real app, you'd verify the JWT token here
    return User(email="demo@example.com")

# Helper for routes that specifically need a demo user
async def get_demo_user():
    return User(email="judge@google-hackathon.com")