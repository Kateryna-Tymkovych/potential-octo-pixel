# FastAPI Manual Authentication System

A secure manual authentication system built with **FastAPI**, **SQLAlchemy** (async/SQLite), and **JWT** (JSON Web Tokens) with manual refresh token rotation and Role-Based Access Control (RBAC).

## Features
- **User Registration & Login**: Custom email-password registration and validation.
- **Access & Refresh Tokens**: Short-lived Access Tokens (JWT) inside the JSON response and long-lived Refresh Tokens in secure `httpOnly` cookies.
- **Token Rotation (Security)**: Rotation of refresh tokens on refresh to mitigate theft/replay attacks. Old refresh tokens are blacklisted immediately.
- **RBAC (Role-Based Access Control)**: Restrict endpoints to specific roles (e.g., `admin` or `user`) using custom FastAPI dependency class factories.

## Project Structure
```text
.
├── app/
│   ├── api/
│   │   ├── deps.py          # FastAPI dependency injection (get_current_user, RoleChecker)
│   │   └── endpoints/
│   │       └── auth.py      # Registration, login, refresh, and logout endpoints
│   ├── core/
│   │   ├── config.py        # Settings definition with pydantic-settings
│   │   └── security.py      # JWT helpers and hashing (bcrypt)
│   ├── db/
│   │   └── session.py       # Async SQLAlchemy engine and session dependency
│   ├── models/
│   │   ├── base.py          # Declarative Base
│   │   ├── token.py         # Blacklisted token model
│   │   └── user.py          # User model
│   └── main.py              # Application entrypoint & protected test routes
├── tests/                   # Integration and unit tests
├── requirements.txt         # Project dependencies
└── README.md                # Documentation
```

## Installation & Setup

1. **Clone and Navigate**:
   ```bash
   cd fastapi-auth-system
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The interactive documentation will be available at:
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Configuration

Settings are managed via Pydantic in `app/core/config.py` and can be customized using a local `.env` file:

- `SECRET_KEY`: Long, cryptographically secure secret string.
- `ALGORITHM`: Token algorithm (default: `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Expiration time for access tokens (default: `15` minutes).
- `REFRESH_TOKEN_EXPIRE_DAYS`: Expiration time for refresh tokens (default: `7` days).

## API Endpoints

### Authentication

#### Register a New User
- **URL**: `POST /auth/register`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "role": "user"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "is_active": true
  }
  ```

#### Login
- **URL**: `POST /auth/login`
- **Body (Form-Data)**:
  - `username`: `user@example.com`
  - `password`: `password123`
- **Response** (200 OK):
  - **Body**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
      "token_type": "bearer"
    }
    ```
  - **Cookies**: Sets `refresh_token` as a secure, `httpOnly` cookie.

#### Refresh Tokens (Rotation)
- **URL**: `POST /auth/refresh`
- **Cookies Required**: `refresh_token`
- **Response** (200 OK):
  - **Body**: New access token.
  - **Cookies**: Sets a *new* rotated `refresh_token` in cookies; the previous one is blacklisted.

#### Logout
- **URL**: `POST /auth/logout`
- **Cookies Required**: `refresh_token`
- **Response** (200 OK): Blacklists the refresh token and clears the `refresh_token` cookie.

### Protected Test Routes

- `GET /user-only`: Accessible by users with `user` or `admin` roles. Requires Bearer token.
- `GET /admin-only`: Accessible only by users with the `admin` role. Requires Bearer token.

## Running Tests

Run the comprehensive test suite (unit and integration tests) using:

```bash
pytest -v
```
