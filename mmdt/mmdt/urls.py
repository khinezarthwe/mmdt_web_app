"""
URL configuration for mmdt project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import logging

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.schemas import get_schema_view
from rest_framework.schemas.openapi import SchemaGenerator

from api.views import AdminTokenView, SwaggerUIView, UserDetailByEmailView

logger = logging.getLogger(__name__)


def ensure_json_serializable(obj):
    """Recursively convert tuples to lists and ensure all values are JSON-serializable."""
    if isinstance(obj, tuple):
        return list(obj)
    elif isinstance(obj, dict):
        return {key: ensure_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [ensure_json_serializable(item) for item in obj]
    else:
        return obj


class CustomSchemaGenerator(SchemaGenerator):
    """Add JWT bearer auth, email query parameter, and enhance /auth/token documentation."""

    def get_paths(self, request=None):
        """Override to ensure API paths are included."""
        # Get paths from parent class
        paths = super().get_paths(request) or {}
        
        # Debug: log what paths were found
        logger.debug(f"Schema generator found {len(paths)} paths: {list(paths.keys())}")
        
        return paths

    def get_schema(self, *args, **kwargs):
        try:
            schema = super().get_schema(*args, **kwargs)
            if not schema:
                return schema

            # Ensure OpenAPI version is set
            if "openapi" not in schema:
                schema["openapi"] = "3.0.2"

            # Add Bearer auth security scheme so Swagger UI shows the Authorize button.
            components = schema.setdefault("components", {})
            security_schemes = components.setdefault("securitySchemes", {})
            security_schemes["bearerAuth"] = {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
            # Ensure security is a list, not a tuple
            schema["security"] = [{"bearerAuth": []}]

            paths = schema.get("paths") or {}

            # Enhance POST /auth/token with proper request/response schemas
            token_path_item = paths.get("/auth/token")
            if token_path_item and "post" in token_path_item:
                post_op = token_path_item["post"]
                # Add request body schema
                post_op["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["username", "password"],
                            "properties": {
                                "username": {
                                    "type": "string",
                                    "description": "Admin username",
                                    "example": "admin",
                                },
                                "password": {
                                    "type": "string",
                                    "format": "password",
                                    "description": "Admin password",
                                    "example": "your-password",
                                },
                            },
                        },
                    }
                },
                }
                # Add response schemas
                responses = post_op.setdefault("responses", {})
                responses["200"] = {
                "description": "Successfully authenticated. Returns access token.",
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "access_token": {
                                    "type": "string",
                                    "description": "JWT access token (valid for 15 minutes)",
                                    "example": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                                },
                                "expires_in": {
                                    "type": "integer",
                                    "description": "Token expiration time in seconds",
                                    "example": 900,
                                },
                                "token_type": {
                                    "type": "string",
                                    "description": "Token type",
                                    "example": "Bearer",
                                },
                            },
                        },
                    }
                },
                }
                responses["400"] = {
                    "description": "Bad request - missing username or password",
                    "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "detail": {
                                    "type": "string",
                                    "example": "Username and password are required.",
                                }
                            },
                        },
                    }
                },
                }
                responses["401"] = {
                    "description": "Unauthorized - invalid credentials or not an admin user",
                    "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "detail": {
                                    "type": "string",
                                    "example": "Invalid credentials or not an admin user.",
                                }
                            },
                        },
                    }
                },
                }
                # Update description
                post_op["summary"] = "Obtain JWT access token for admin users"
                post_op["description"] = (
                    "Authenticate with admin credentials to receive a short-lived (15 minutes) "
                    "JWT access token. Only users with admin privileges (is_staff=True) can obtain tokens."
                )
                # Explicitly remove security requirement - this is the login endpoint
                # and doesn't require authentication (overrides global security setting)
                post_op["security"] = []

            # Ensure the GET /api/users operation has an `email` query parameter.
            user_path_item = paths.get("/api/users")
            if user_path_item and "get" in user_path_item:
                get_op = user_path_item["get"]
                params = get_op.setdefault("parameters", [])
                has_email_param = any(
                    p.get("name") == "email" and p.get("in") == "query" for p in params
                )
                if not has_email_param:
                    params.append(
                        {
                            "name": "email",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "email"},
                            "description": "Email address of the user to look up.",
                            "example": "mmdt@example.com",
                        }
                    )
                # Add response schemas for /api/users
                responses = get_op.setdefault("responses", {})
                responses["200"] = {
                    "description": "Successfully retrieved user information",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {
                                        "type": "string",
                                        "format": "email",
                                        "example": "mmdt@example.com",
                                    },
                                    "enddate": {
                                        "type": "string",
                                        "format": "date-time",
                                        "nullable": True,
                                        "description": "User subscription expiry date (ISO 8601 format) or null",
                                        "example": "2025-12-31T23:59:59Z",
                                    },
                                },
                            },
                        },
                    }
                },
                responses["400"] = {
                    "description": "Bad request - missing email parameter",
                }
                responses["401"] = {
                    "description": "Unauthorized - missing or invalid JWT token",
                }
                responses["403"] = {
                    "description": "Forbidden - authenticated user is not an admin",
                }
                responses["404"] = {
                    "description": "Not found - user with given email does not exist",
                }

            # Ensure all values are JSON-serializable (convert tuples to lists)
            schema = ensure_json_serializable(schema)
            return schema
        except Exception as e:
            # Log the error for debugging but don't crash the endpoint
            logger.error(
                f"Error in CustomSchemaGenerator.get_schema(): {e}",
                exc_info=True,
                extra={"exception_type": type(e).__name__}
            )
            # Fallback: return base schema without customizations
            try:
                base_schema = super().get_schema(*args, **kwargs)
                # Ensure it has the openapi version field
                if base_schema and "openapi" not in base_schema:
                    base_schema["openapi"] = "3.0.2"
                # Ensure all values are JSON-serializable
                base_schema = ensure_json_serializable(base_schema)
                return base_schema
            except Exception as fallback_error:
                # If even the base schema fails, return a minimal valid OpenAPI schema
                logger.error(
                    f"Error in base schema generation: {fallback_error}",
                    exc_info=True
                )
                # Return a minimal valid OpenAPI 3.0 schema
                return {
                    "openapi": "3.0.2",
                    "info": {
                        "title": "MMDT API",
                        "version": "1.0.0",
                        "description": "OpenAPI schema for token and user endpoints."
                    },
                    "paths": {},
                    "components": {}
                }


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('blog.urls')),
    path('polls/', include('polls.urls', namespace='polls')),
    path('survey/', include('survey.urls', namespace='survey')),
    path('surveys/', include('djf_surveys.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('auth/token', AdminTokenView.as_view(), name='auth-token'),
    path('api/users', UserDetailByEmailView.as_view(), name='api-user-by-email'),
    path('api/docs/', SwaggerUIView.as_view(), name='swagger-ui'),
    path(
        'api/schema/',
        get_schema_view(
            title='MMDT API',
            description='OpenAPI schema for token and user endpoints.',
            version='1.0.0',
            public=True,
            permission_classes=[AllowAny],
            generator_class=CustomSchemaGenerator,
        ),
        name='openapi-schema',
    ),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
