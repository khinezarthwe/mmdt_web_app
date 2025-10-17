from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import UserProfile
from .serializers import UserSerializer, UserDetailSerializer


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to view their own data,
    or admins to view all data.
    """

    def has_object_permission(self, request, view, obj):
        # Admin users can access any user's data
        if request.user.is_staff or request.user.is_superuser:
            return True
        # Regular users can only access their own data
        return obj == request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user data.

    Provides read-only access to user information.
    Regular users can only access their own data.
    Admin users can access all user data.

    list: Get a list of users (admin only)
    retrieve: Get details of a specific user
    me: Get current user's information
    """
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        """Use detailed serializer for single user, basic for list."""
        if self.action == 'retrieve' or self.action == 'me':
            return UserDetailSerializer
        return UserSerializer

    def get_queryset(self):
        """
        Limit queryset to current user unless user is admin.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admins can see all users
            return User.objects.select_related('profile').all()
        # Regular users can only see themselves
        return User.objects.filter(id=user.id).select_related('profile')

    def list(self, request):
        """
        List all users - admin only.

        Regular users will receive a 403 Forbidden error.
        """
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "You do not have permission to view all users."},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Get details of a specific user by ID.

        Example: GET /api/users/1/
        """
        # Check if user is trying to access their own data or is admin
        if not (request.user.is_staff or request.user.is_superuser):
            if str(request.user.id) != str(pk):
                return Response(
                    {"detail": "You do not have permission to access this user's data."},
                    status=status.HTTP_403_FORBIDDEN
                )

        try:
            user = User.objects.select_related('profile').get(pk=pk)
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get current authenticated user's information.

        Example: GET /api/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
