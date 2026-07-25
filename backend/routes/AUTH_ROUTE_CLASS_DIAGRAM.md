# Authentication Route Class Diagram

```mermaid
classDiagram
    direction LR

    class AuthRouter {
        <<auth.py / APIRouter>>
        +register(payload) User
        +login(form_data) TokenResponse
        +refresh_token(payload) TokenResponse
        +logout(current_user) MessageResponse
        +forgot_password(payload) MessageResponse
        +reset_password(payload) MessageResponse
        +get_current_profile(current_user) User
    }

    class AuthService {
        <<service>>
        +hash_password(password) str
        +verify_password(password, hash) bool
        +authenticate_user(email, password) User
        +create_access_token(subject) str
        +create_refresh_token(subject) str
        +decode_token(token) dict
    }

    class User {
        <<model>>
    }

    class MongoDB {
        <<database dependency>>
        +users
    }

    AuthRouter --> AuthService : delegates authentication
    AuthRouter --> User : request and response model
    AuthService --> MongoDB : reads and writes users
```

## Imports for `auth.py`

```python
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from ..database import get_database
from ..models import User
```

If authentication logic is moved out of the route, create `services/auth_service.py` and also use:

```python
from ..services.auth_service import AuthService
```

