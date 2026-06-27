from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.hashers import check_password, make_password


UserModel = get_user_model()

_DUMMY_HASH = make_password('not-a-real-password')


class EmailBackend(ModelBackend):
    """Authenticate by case-insensitive email while mitigating user enumeration."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')
        if email is None or password is None:
            return None
        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            check_password(password, _DUMMY_HASH)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
