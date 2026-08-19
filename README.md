# FastAPI Authentication System

A production-ready authentication system built with FastAPI, SQLAlchemy, and JWT.

## Features

- **JWT Authentication**: Access tokens (15m) and Refresh tokens (7d).
- **Refresh Token Rotation**: Automatic rotation and revocation of old tokens.
- **RBAC**: Role-Based Access Control (Admin, User, Guest).
- **Secure Cookies**: Refresh tokens stored in HttpOnly, Secure, SameSite cookies.
- **Password Hashing**: Bcrypt with Passlib.

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once the app is running, visit:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Roles

- `admin`: Full access to all endpoints.
- `user`: Access to user and guest endpoints.
- `guest`: Access to guest endpoints only.

## Testing

Run tests with pytest:
```bash
pytest
```
