from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class UserInfo(BaseModel):
    email: str
    name: str
    role: str
    monday_user_id: str = ""


class LoginResponse(BaseModel):
    access_token: str
    user: UserInfo
