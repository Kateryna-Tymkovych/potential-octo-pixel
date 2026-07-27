# Secure Custom Authentication & Authorization System

A production-ready, secure JWT-based authentication and role-based access control (RBAC) system built with **FastAPI**, **SQLAlchemy (SQLite)**, and **Pydantic Settings**. Fully compatible with Python 3.13+.

---

## 🚀 Key Features

* **Secure Password Hashing:** Uses standard `bcrypt` hashing for secure user passwords, fully avoiding unmaintained Passlib library compatibility bugs.
* **JWT Access & Refresh Tokens:** Issues short-lived Access Tokens (Bearer) and long-lived Refresh Tokens.
* **Token Rotation (Security Spec):** Implements one-time-use refresh tokens that rotate upon every `/refresh` request.
* **Token Reuse Detection & Revocation:** Reusing an old refresh token automatically triggers the revocation of all active sessions for that user for supreme security.
* **HttpOnly Refresh Cookies:** Refresh tokens are set as `httpOnly`, `samesite="lax"` cookies to guard against Cross-Site Scripting (XSS).
* **Role-Based Access Control (RBAC):** Flexible and reusable class-based `RoleChecker` dependency to guard endpoints based on roles (e.g. `admin`, `user`).
* **Interactive OpenAPI Docs:** Fully auto-documented endpoints out of the box with OpenAPI standards at `/docs`.

---

## 🛠️ Project Structure

```text
├── app/
│   ├── api/
│   │   ├── deps.py             # Auth & RBAC FastAPI dependencies
│   │   └── endpoints/
│   │       ├── auth.py         # Login, register, refresh, logout
│   │       └── protected.py    # Admin & user protected endpoints
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   └── security.py         # JWT and password hashing helpers
│   ├── db/
│   │   └── session.py          # SQLAlchemy session & database initialization
│   ├── models/
│   │   ├── token.py            # RefreshToken database model
│   │   └── user.py             # User database model
│   ├── schemas/
│   │   └── user.py             # Pydantic schemas for request/response validation
│   └── main.py                 # FastAPI App Entrypoint
├── tests/
│   ├── conftest.py             # Pytest configuration & in-memory SQLite fixtures
│   ├── test_auth_flow.py       # JWT Login, Logout, & Rotation integration tests
│   ├── test_rbac.py            # Role-Based Access Control integration tests
│   └── test_registration.py    # User creation and unique email tests
├── .env                        # Environment Secrets (configured)
├── requirements.txt            # Project dependencies
└── README.md                   # This file
```

---

## ⚙️ Configuration (`.env`)

The application is configured using a `.env` file that Pydantic Settings securely parses:

* `SECRET_KEY`: Secret used for signing JWTs.
* `ALGORITHM`: Encryption algorithm (default: `HS256`).
* `ACCESS_TOKEN_EXPIRE_MINUTES`: Lifetime of access tokens (default: `15`).
* `REFRESH_TOKEN_EXPIRE_DAYS`: Lifetime of refresh tokens (default: `7`).
* `DATABASE_URL`: SQLAlchemy connection URL (default: `sqlite:///./auth.db`).

---

## 📦 Getting Started

### 1. Install Dependencies

Ensure you have Python 3.12+ or Python 3.13+ installed, then run:

```bash
pip install -r requirements.txt
```

### 2. Start the Application

Start the FastAPI application locally using `uvicorn`:

```bash
uvicorn app.main:app --reload
```

The server will be running on `http://127.0.0.1:8000`.

### 3. Interactive API Docs

Once running, visit `http://127.0.0.1:8000/docs` to test registration, login, token refresh, logout, and protected role-restricted routes directly in your browser.

---

## 🧪 Running Tests

A comprehensive integration test suite is provided. To run all unit and integration tests using an isolated in-memory database:

```bash
python3 -m pytest
```

---

## 🔒 API Endpoints & Token Flow

### 1. **User Registration**
* **Endpoint:** `POST /auth/register`
* **Body:** JSON `{"email": "user@example.com", "password": "securepassword"}`
* **Response:** Created User object (excludes password).

### 2. **Login**
* **Endpoint:** `POST /auth/login`
* **Body:** Form Data `username=user@example.com&password=securepassword`
* **Response:**
  * **JSON Body:** `{"access_token": "JWT_ACCESS_TOKEN", "token_type": "bearer"}`
  * **HttpOnly Cookie:** `refresh_token=JWT_REFRESH_TOKEN; Path=/; HttpOnly; SameSite=Lax`

### 3. **Token Rotation / Refresh**
* **Endpoint:** `POST /auth/refresh`
* **Details:** Expects the active `refresh_token` in the cookies. If valid, the old token is revoked, and a new rotated access/refresh pair is returned.

### 4. **Logout**
* **Endpoint:** `POST /auth/logout`
* **Details:** Revokes the active refresh token in the database and clears the cookie.

### 5. **Protected Endpoints (RBAC)**
* **User Area:** `GET /api/user-area` (Access: `user`, `admin`)
* **Admin-Only:** `GET /api/admin-only` (Access: `admin` only)
* **Usage:** Pass the access token in the headers as: `Authorization: Bearer <access_token>`
