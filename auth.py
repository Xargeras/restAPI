from functools import wraps
import jwt
from sanic import text


def check_token(request):
    if not request.token:
        return False

    try:
        token = jwt.decode(
            request.token, request.app.config.SECRET, algorithms=["HS256"]
        )
        return token
    except jwt.exceptions.InvalidTokenError:
        return False


def protected(wrapped):
    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):
            token = check_token(request)

            if token:
                response = await f(request, *args, **kwargs)

                if request.path.find('admin') != -1 and not token['admin']:
                    return text("Permission denied.", 403)
                if request.path.find('api') != -1 and not token['active'] and not token['admin']:
                    return text("Permission denied, please activate your account.", 403)
                return response
            else:
                return text("You are unauthorized.", 401)

        return decorated_function

    return decorator(wrapped)
