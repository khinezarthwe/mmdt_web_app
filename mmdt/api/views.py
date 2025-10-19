from django.shortcuts import render

# Create your views here.
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from .serializers import UserSerializer

class CustomAuthToken(ObtainAuthToken):
    """
    Handles POST requests to /api/auth/token/ to authenticate a user
    and return an auth token.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username
        })

class CurrentUserView(generics.RetrieveAPIView):
    """
    Handles GET /api/users/me/ to return the profile of the
    currently authenticated user.
    """
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class UserDetailView(generics.RetrieveAPIView):
    """
    Handles GET /api/users/<id>/ to return the profile of a specific user.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'pk'  # Use the primary key (id) from the URL