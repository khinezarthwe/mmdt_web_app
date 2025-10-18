from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User


class CustomAuthToken(ObtainAuthToken):
    """
    Custom authentication endpoint that returns user info along with token.

    POST /api/auth/token/
    Body: {"username": "user", "password": "pass"}
    or
    Body: {"email": "user@example.com", "password": "pass"}
    """

    def post(self, request, *args, **kwargs):
        # Check if email is provided instead of username
        data = request.data.copy()
        if 'email' in data and 'username' not in data:
            # Try to find user by email
            try:
                user = User.objects.get(email=data['email'])
                data['username'] = user.username
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid email or password'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Use the parent class method with modified data
        serializer = self.serializer_class(data=data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'username': user.username
        })
