from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import UserProfile, UserSession
from .serializers import UserSerializer, UserDetailSerializer, UserSessionSerializer


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
    queryset = User.objects.all().order_by('-date_joined')
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
    @extend_schema(
        summary="Get current user info",
        description="Retrieve information about the currently authenticated user.",
        responses={200: UserDetailSerializer},
        tags=['Users']
    )
    def me(self, request):
        """
        Get current authenticated user's information.

        Example: GET /api/v1/auth/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for managing user sessions.

    Provides read-only access to session information and
    actions to revoke sessions.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSessionSerializer

    def get_queryset(self):
        """
        Return sessions for the current user only.
        Admins can see all sessions.
        """
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return UserSession.objects.all().select_related('user').order_by('-created_at')
        return UserSession.objects.filter(user=user).order_by('-created_at')

    @extend_schema(
        summary="List user sessions",
        description="Get all active sessions for the current user. Admins can see all sessions.",
        responses={200: UserSessionSerializer(many=True)},
        tags=['Sessions']
    )
    def list(self, request):
        """List all active sessions for current user."""
        queryset = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get session details",
        description="Retrieve detailed information about a specific session.",
        responses={200: UserSessionSerializer},
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='Session ID'
            )
        ],
        tags=['Sessions']
    )
    def retrieve(self, request, pk=None):
        """Get details of a specific session."""
        try:
            session = self.get_queryset().get(pk=pk)

            # Check permission
            if not (request.user.is_staff or request.user.is_superuser):
                if session.user != request.user:
                    return Response(
                        {"detail": "You do not have permission to access this session."},
                        status=status.HTTP_403_FORBIDDEN
                    )

            serializer = self.get_serializer(session)
            return Response(serializer.data)

        except UserSession.DoesNotExist:
            return Response(
                {"detail": "Session not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    @extend_schema(
        summary="Revoke a session",
        description="Revoke a specific session by ID. This will mark the session as inactive and blacklist the token.",
        responses={
            200: {'description': 'Session revoked successfully'},
            403: {'description': 'Permission denied'},
            404: {'description': 'Session not found'}
        },
        tags=['Sessions']
    )
    def revoke(self, request, pk=None):
        """Revoke a specific session."""
        try:
            session = self.get_queryset().get(pk=pk, is_active=True)

            # Check permission
            if not (request.user.is_staff or request.user.is_superuser):
                if session.user != request.user:
                    return Response(
                        {"detail": "You do not have permission to revoke this session."},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Revoke session
            session.revoke()

            # Blacklist the refresh token
            try:
                token = OutstandingToken.objects.get(jti=session.refresh_token_jti)
                BlacklistedToken.objects.get_or_create(token=token)
            except OutstandingToken.DoesNotExist:
                pass

            return Response({
                'message': 'Session revoked successfully',
                'session_id': session.id
            })

        except UserSession.DoesNotExist:
            return Response(
                {"detail": "Active session not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    @extend_schema(
        summary="Revoke all sessions",
        description="Revoke all active sessions for the current user except optionally the current one.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'keep_current': {
                        'type': 'boolean',
                        'description': 'Whether to keep the current session active',
                        'default': False
                    }
                }
            }
        },
        responses={200: {'description': 'Sessions revoked successfully'}},
        tags=['Sessions']
    )
    def revoke_all(self, request):
        """Revoke all sessions except optionally the current one."""
        keep_current = request.data.get('keep_current', False)
        sessions = self.get_queryset().filter(is_active=True)

        # If keeping current, we would need to identify it from the JWT
        # For now, revoke all
        revoked_count = 0
        for session in sessions:
            session.revoke()
            try:
                token = OutstandingToken.objects.get(jti=session.refresh_token_jti)
                BlacklistedToken.objects.get_or_create(token=token)
                revoked_count += 1
            except OutstandingToken.DoesNotExist:
                pass

        return Response({
            'message': f'{revoked_count} session(s) revoked successfully',
            'revoked_count': revoked_count
        })
