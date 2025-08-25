from ninja.security import HttpBearer
from django.contrib.auth import get_user_model
from jwt import ExpiredSignatureError, InvalidTokenError
from app.services.custom_user import CustomUserService
from django.conf import settings
from ninja.errors import HttpError
from app.common.default.utils import is_debug

User = get_user_model()


class JWTAuth(HttpBearer):
    def authenticate(self, request, token: str):
        try:
            user_service: CustomUserService = CustomUserService(
                jwt_secret_key=settings.JWT_SECRET_KEY,
                jwt_algorithm=settings.JWT_ALGORITHM,
                jwt_expiration_time=settings.JWT_EXPIRATION_TIME,
                jwt_refresh_expiration_time=settings.JWT_REFRESH_EXPIRATION_TIME,
            )
            payload = user_service.verify_jwt_token(token)
            if payload.get("type") != "access":
                return None
            # Convert sub from string back to int for database query
            user_id = int(payload["sub"])
            return User.objects.get(id=user_id)
        except ExpiredSignatureError:
            raise HttpError(401, "Token expired")

        except InvalidTokenError:
            raise HttpError(401, "Invalid token")
        except User.DoesNotExist:
            raise HttpError(401, "User not found")
        except ValueError:
            raise HttpError(401, "Invalid token")
        except Exception as e:
            message = (
                "An error occurred while authenticating the user"
                if not is_debug()
                else str(e)
            )
            raise HttpError(500, message)
