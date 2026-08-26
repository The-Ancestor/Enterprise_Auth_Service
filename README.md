# Enterprise Authentication Service

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-e91e63.svg)](https://docs.pydantic.dev/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests: Pytest](https://img.shields.io/badge/tests-pytest%20100%25%20passing-brightgreen.svg)](https://docs.pytest.org/)

A production-ready, test-driven authentication microservice built with **FastAPI**, **SQLAlchemy**, and **Pydantic v2**. Designed around zero-trust security patterns, stateless JWT authorization, stateful refresh token rotation, single-use token revocation, and device telemetry tracking.

---

## Architecture & Security Blueprint

* **Stateless Access Control**: Short-lived JWT access tokens signed via HMAC-SHA256.
* **Stateful Refresh Token Rotation**: Cryptographically secure `secrets.token_hex(32)` tokens stored as **SHA-256 hashes** to eliminate cleartext storage risks.
* **Single-Use Revocation**: Consuming a refresh token invalidates its database record immediately, preventing token replay attacks.
* **Device Telemetry & ORM Serialization**: Leverages SQLAlchemy ORM relationships to capture and serialize active sessions, `User-Agent` headers, and expiration dates via Pydantic v2 (`from_attributes=True`).
* **Environment-Driven Configuration**: Managed cleanly via `python-dotenv` and isolated `os.getenv` loading.
* **Isolated TDD Suite**: 100% endpoint test coverage using `pytest` and isolated database sessions.

---

## Authentication & Token Flow

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) |
| **ORM & Database** | [SQLAlchemy](https://www.sqlalchemy.org/) + SQLite / PostgreSQL |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/latest/) |
| **Cryptography & Auth** | `PyJWT`, `passlib[bcrypt]`, `secrets`, `hashlib` (SHA-256) |
| **Config Management** | `python-dotenv` |
| **Test Automation** | `pytest`, `httpx` |

---

## Setup & Local Installation

### Prerequisites
* Python 3.11+
* Git

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone [https://github.com/YOUR_GITHUB_USERNAME/Enterprise-Auth-Service.git](https://github.com/YOUR_GITHUB_USERNAME/Enterprise-Auth-Service.git)
   cd Enterprise-Auth-Service

   python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
