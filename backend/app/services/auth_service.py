import json
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError


class AuthService:
    def __init__(
        self,
        users_config: str,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expire_minutes: int = 480,
    ):
        self._users: list[dict[str, str]] = json.loads(users_config) if users_config else []
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._jwt_expire_minutes = jwt_expire_minutes

    def authenticate(self, email: str, password: str) -> dict[str, str] | None:
        for user in self._users:
            if user["email"] == email and user["password"] == password:
                return {
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "monday_user_id": user.get("monday_user_id", ""),
                }
        return None

    def create_token(self, user: dict[str, str]) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._jwt_expire_minutes)
        payload = {
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "monday_user_id": user.get("monday_user_id", ""),
            "exp": expire,
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)

    def verify_token(self, token: str) -> dict[str, Any] | None:
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            return payload
        except JWTError:
            return None
