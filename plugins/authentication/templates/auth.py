from .config import (
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_NAME,
    DATABASE_USERNAME,
    DATABASE_PASSWORD,
    REDIS_HOST,
    REDIS_PORT,
)


def authenticate(username: str, password: str):

    # Authentication implementation
    # will be added here.

    return {
        "authenticated": False,
        "username": username
    }