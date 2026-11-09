from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.domain.exceptions import AuthenticationError

# bcrypt only uses the first 72 bytes of the password; newer versions raise instead of truncating.
_BCRYPT_MAX_BYTES = 72


class BcryptPasswordHasher:
    def hash(self, password: str) -> str:
        return bcrypt.hashpw(self._encode(password), bcrypt.gensalt()).decode()

    def verify(self, password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(self._encode(password), hashed.encode())
        except ValueError:
            return False

    @staticmethod
    def _encode(password: str) -> bytes:
        return password.encode()[:_BCRYPT_MAX_BYTES]


class JwtTokenService:
    def __init__(self, secret: str, algorithm: str, expire_minutes: int) -> None:
        self.secret = secret
        self.algorithm = algorithm
        self.expire_minutes = expire_minutes

    def create_access_token(self, subject: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "iat": now,
            "exp": now + timedelta(minutes=self.expire_minutes),
            "type": "access",
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def decode_subject(self, token: str) -> str:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm],  # explicit list: prevents "alg": "none" attacks
                options={"require": ["sub", "exp"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid or expired token") from exc
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        return str(payload["sub"])
