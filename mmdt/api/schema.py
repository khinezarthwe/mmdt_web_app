"""
Custom OpenAPI schema generator for API documentation.
"""
from rest_framework.schemas.openapi import SchemaGenerator


class CustomSchemaGenerator(SchemaGenerator):
    """Add JWT bearer auth, email query parameter, and enhance /auth/token documentation."""

    def get_schema(self, *args, **kwargs):
        schema = super().get_schema(*args, **kwargs)
        if not schema:
            return schema

        # Add Bearer auth security scheme so Swagger UI shows the Authorize button.
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        schema["security"] = [{"bearerAuth": []}]

        paths = schema.get("paths") or {}

        self._enhance_token_endpoint(paths)
        self._enhance_users_endpoint(paths)
        self._enhance_users_telegram_endpoint(paths)
        self._enhance_renewal_endpoint(paths)

        return schema

    def _enhance_token_endpoint(self, paths):
        """Enhance POST /auth/token with proper request/response schemas."""
        token_path_item = paths.get("/api/auth/token")
        if not token_path_item or "post" not in token_path_item:
            return

        post_op = token_path_item["post"]
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

        post_op["summary"] = "Obtain JWT access token for admin users"
        post_op["description"] = (
            "Authenticate with admin credentials to receive a short-lived (15 minutes) "
            "JWT access token. Only users with admin privileges (is_staff=True) can obtain tokens."
        )
        post_op["security"] = []

    def _enhance_users_endpoint(self, paths):
        """Ensure the GET /api/users operation has an email query parameter."""
        user_path_item = paths.get("/api/users")
        if not user_path_item or "get" not in user_path_item:
            return

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
                }
            },
        }
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

    def _enhance_users_telegram_endpoint(self, paths):
        """Ensure the GET /api/users/telegram operation has a telegram_name query parameter."""
        user_path_item = paths.get("/api/users/telegram")
        if not user_path_item or "get" not in user_path_item:
            return

        get_op = user_path_item["get"]
        get_op["summary"] = "Get user details by telegram username"
        get_op["description"] = (
            "Retrieve user information by their Telegram username. "
            "Returns the same response format as the email lookup endpoint, "
            "plus a registration_open flag indicating whether cohort registration is currently open."
        )

        params = get_op.setdefault("parameters", [])
        has_telegram_param = any(
            p.get("name") == "telegram_name" and p.get("in") == "query" for p in params
        )
        if not has_telegram_param:
            params.append(
                {
                    "name": "telegram_name",
                    "in": "query",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": "Telegram username of the user to look up (with or without @ prefix).",
                    "example": "username123",
                }
            )

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
                                "description": "User's email address",
                                "example": "user@example.com",
                            },
                            "enddate": {
                                "type": "string",
                                "format": "date-time",
                                "nullable": True,
                                "description": "User subscription expiry date (ISO 8601 format) or null",
                                "example": "2025-12-31T23:59:59Z",
                            },
                            "registration_open": {
                                "type": "boolean",
                                "description": "Whether cohort registration is currently open",
                                "example": True,
                            },
                        },
                    },
                }
            },
        }
        responses["400"] = {
            "description": "Bad request - missing telegram_name parameter",
        }
        responses["401"] = {
            "description": "Unauthorized - missing or invalid JWT token",
        }
        responses["403"] = {
            "description": "Forbidden - authenticated user is not an admin",
        }
        responses["404"] = {
            "description": "Not found - user with given telegram username does not exist",
        }
        responses["500"] = {
            "description": "Server error - error occurred while looking up user",
        }

    def _enhance_renewal_endpoint(self, paths):
        """Enhance POST /api/user/request_renew with proper request/response schemas."""
        renewal_path_item = paths.get("/api/user/request_renew")
        if not renewal_path_item or "post" not in renewal_path_item:
            return

        post_op = renewal_path_item["post"]
        post_op["summary"] = "Request membership renewal"
        post_op["description"] = (
            "Submit a renewal request for an existing active user. "
            "Both email and telegram_name are required and must match the user's stored records. "
            "Returns a Google Drive folder URL for payment proof upload."
        )

        post_op["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["email", "telegram_name", "plan"],
                        "properties": {
                            "email": {
                                "type": "string",
                                "format": "email",
                                "description": "User's email address",
                                "example": "user@example.com",
                            },
                            "telegram_name": {
                                "type": "string",
                                "description": "User's Telegram username",
                                "example": "username123",
                            },
                            "plan": {
                                "type": "string",
                                "enum": ["6month", "annual"],
                                "description": "Subscription plan for renewal",
                                "example": "6month",
                            },
                        },
                    },
                }
            },
        }

        responses = post_op.setdefault("responses", {})
        responses["200"] = {
            "description": "Renewal request submitted successfully",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "example": "success",
                            },
                            "message": {
                                "type": "string",
                                "example": "Renewal request received",
                            },
                            "upload_url": {
                                "type": "string",
                                "format": "uri",
                                "description": "Google Drive folder URL for payment proof upload",
                                "example": "https://drive.google.com/drive/folders/...",
                            },
                        },
                    },
                }
            },
        }
        responses["400"] = {
            "description": "Bad request - missing/invalid parameters or email/telegram mismatch",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "example": "error"},
                            "message": {
                                "type": "string",
                                "example": "Email and telegram_name do not match.",
                            },
                        },
                    },
                }
            },
        }
        responses["401"] = {
            "description": "Unauthorized - missing or invalid JWT token",
        }
        responses["403"] = {
            "description": "Forbidden - user account is not active or no active cohort registration window is open",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "example": "error"},
                            "message": {
                                "type": "string",
                                "description": "Either 'User account is not active.' or 'Registration is currently closed. No active cohort registration window is open.'",
                            },
                        },
                    },
                }
            },
        }
        responses["404"] = {
            "description": "User not found or no subscription record",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "example": "error"},
                            "message": {"type": "string", "example": "User not found."},
                        },
                    },
                }
            },
        }
        responses["409"] = {
            "description": "Renewal request already pending",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "example": "pending"},
                            "message": {"type": "string", "example": "Renewal request already submitted."},
                        },
                    },
                }
            },
        }
        responses["500"] = {
            "description": "Server error - failed to generate upload URL",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string", "example": "error"},
                            "message": {"type": "string", "example": "Failed to generate upload URL."},
                        },
                    },
                }
            },
        }
