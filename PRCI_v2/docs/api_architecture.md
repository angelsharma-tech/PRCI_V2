# PRCI v2 API Architecture

## Overview

The PRCI v2 API is built on FastAPI with a modular architecture following industry best practices for production-grade REST APIs.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Web Browser │  │  Mobile App  │  │  Streamlit UI       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┴─────────────────────┘             │
│                          │                                      │
│                    HTTPS / HTTP                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                          ▼                                      │
│                   FastAPI Application                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Middleware Stack                        │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │  │
│  │  │   CORS     │ │ Rate Limit │ │ Security Headers   │   │  │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │  │
│  │  │Req Logging │ │Error Handler│ │ Request ID          │   │  │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│  ┌───────────────────────┼───────────────────────────────────┐ │
│  │                   Router Layer                               │ │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐          │ │
│  │  │ Health │ │  Auth  │ │  Users   │ │Assessments│         │ │
│  │  │/health │ │ /auth  │ │ /users   │ │/assessments│        │ │
│  │  └────────┘ └────────┘ └──────────┘ └──────────┘          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐        │ │
│  │  │Conversations│ │Interventions│ │ Reports  │ │ Admin  │        │ │
│  │  │/conversations│ │/interventions│ │ /reports │ │ /admin │        │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                      │
│  ┌───────────────────────┼───────────────────────────────────┐ │
│  │                 Dependency Injection                       │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │ │
│  │  │  get_db    │ │get_current │ │  require_admin     │   │ │
│  │  │ (Session)  │ │   _user    │ │  (Role check)      │   │ │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                      │
│  ┌───────────────────────┼───────────────────────────────────┐ │
│  │                    Service Layer                             │ │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────────┐   │ │
│  │  │   Auth     │ │ Database   │ │  Persistence       │   │ │
│  │  │  Service   │ │  Service   │ │   Service          │   │ │
│  │  └────────────┘ └────────────┘ └────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                          │                                      │
└──────────────────────────┼──────────────────────────────────────┘
                           │
┌──────────────────────────┼──────────────────────────────────────┐
│                          ▼                                      │
│                   Database Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy ORM + Repository Pattern           │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │  │
│  │  │ Users  │ │Sessions│ │Convos  │ │Messages│          │  │
│  │  │  Repo  │ │  Repo  │ │  Repo  │ │  Repo  │          │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘          │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │  │
│  │  │Assess  │ │ Scores │ │Interven│ │ Reports│          │  │
│  │  │  Repo  │ │  Repo  │ │  Repo  │ │  Repo  │          │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                   ┌──────┴──────┐                               │
│                   │  SQLite/    │                               │
│                   │  PostgreSQL │                               │
│                   └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. API Layer (`api/`)
- **main.py**: FastAPI application factory with lifespan management
- **exceptions.py**: Custom API exceptions with proper HTTP status codes
- **dependencies.py**: Dependency injection for database sessions, authentication, and authorization
- **middleware.py**: Request logging, rate limiting, CORS, security headers

### 2. Authentication Layer (`auth/`)
- **jwt_handler.py**: JWT token creation, verification, and refresh
- **password_handler.py**: Bcrypt password hashing and password reset tokens
- **auth_service.py**: Business logic for login, register, password management

### 3. Schema Layer (`schemas/`)
- Pydantic models for request/response validation
- Base, Create, Update, and Response variants for each entity
- Common schemas for pagination, errors, and success responses

### 4. Router Layer (`routers/`)
- Modular routers for each domain
- Consistent CRUD patterns
- Proper authorization checks

### 5. Service Layer (`services/`)
- Business logic abstraction
- Database service integration
- Streamlit compatibility layer

### 6. Data Layer (`repositories/`)
- Repository pattern implementation
- CRUD operations with error handling
- Domain-specific query methods

## Authentication Flow

```
┌─────────────┐     Register      ┌─────────────┐
│   Client    │ ────────────────> │   /auth     │
│             │                   │  /register  │
│             │ <──────────────── │             │
│             │   Token + User    └─────────────┘
│             │
│             │     Login         ┌─────────────┐
│             │ ────────────────> │   /auth     │
│             │                   │   /login    │
│             │ <──────────────── │             │
│             │   Access Token    └─────────────┘
│             │   Refresh Token
│             │
│             │     API Call      ┌─────────────┐
│             │ ────────────────> │  Protected  │
│             │   Authorization:  │   Route     │
│             │   Bearer <token>  │             │
│             │ <──────────────── │             │
│             │   Data Response   └─────────────┘
│             │
│             │     Refresh       ┌─────────────┐
│             │ ────────────────> │   /auth     │
│             │   Refresh Token   │  /refresh   │
│             │ <──────────────── │             │
│             │   New Tokens      └─────────────┘
```

### JWT Token Structure

**Access Token**:
```json
{
  "sub": "123",
  "email": "user@example.com",
  "role": "USER",
  "exp": 1704067200,
  "iat": 1704063600,
  "jti": "uuid-string",
  "type": "access"
}
```

**Refresh Token**:
```json
{
  "sub": "123",
  "exp": 1704672000,
  "iat": 1704063600,
  "jti": "uuid-string",
  "type": "refresh"
}
```

## Endpoint Documentation

### Health Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Basic health check |
| GET | `/health/ready` | No | Readiness probe |
| GET | `/health/live` | No | Liveness probe |

### Authentication Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Authenticate user |
| POST | `/auth/refresh` | No | Refresh access token |
| POST | `/auth/logout` | Yes | Logout user |
| POST | `/auth/password-reset-request` | No | Request password reset |
| POST | `/auth/password-reset` | No | Confirm password reset |
| POST | `/auth/change-password` | Yes | Change password |

### User Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/users/me` | Yes | Get current user profile |
| PUT | `/users/me` | Yes | Update current user |
| DELETE | `/users/me` | Yes | Delete current user |
| GET | `/users/{id}` | Yes | Get user by ID |
| GET | `/users` | Admin | List all users |
| PUT | `/users/{id}/status` | Admin | Update user status |
| PUT | `/users/{id}/role` | Admin | Update user role |
| GET | `/users/statistics/overview` | Admin | User statistics |

### Assessment Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/assessments` | Yes | Create assessment |
| GET | `/assessments/{id}` | Yes | Get assessment |
| GET | `/assessments` | Yes | List user assessments |
| PUT | `/assessments/{id}` | Yes | Update assessment |
| POST | `/assessments/{id}/complete` | Yes | Complete assessment |
| POST | `/assessments/{id}/scores` | Yes | Add score |
| DELETE | `/assessments/{id}` | Yes | Delete assessment |
| GET | `/assessments/statistics/overview` | Yes | Assessment statistics |

### Conversation Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/conversations` | Yes | Create conversation |
| GET | `/conversations/{id}` | Yes | Get conversation |
| GET | `/conversations` | Yes | List conversations |
| PUT | `/conversations/{id}` | Yes | Update conversation |
| POST | `/conversations/{id}/messages` | Yes | Add message |
| PUT | `/conversations/{id}/messages/{mid}/feedback` | Yes | Message feedback |
| DELETE | `/conversations/{id}` | Yes | Delete conversation |
| GET | `/conversations/statistics/overview` | Yes | Conversation statistics |

### Intervention Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/interventions/templates` | Yes | List templates |
| GET | `/interventions/templates/{id}` | Yes | Get template |
| POST | `/interventions/templates` | Admin | Create template |
| PUT | `/interventions/templates/{id}` | Admin | Update template |
| GET | `/interventions/user` | Yes | List user interventions |
| GET | `/interventions/user/{id}` | Yes | Get user intervention |
| POST | `/interventions/recommend` | Yes | Recommend intervention |
| PUT | `/interventions/user/{id}/accept` | Yes | Accept intervention |
| PUT | `/interventions/user/{id}` | Yes | Update progress |
| PUT | `/interventions/user/{id}/complete` | Yes | Complete intervention |
| DELETE | `/interventions/user/{id}` | Yes | Delete user intervention |
| GET | `/interventions/statistics/overview` | Yes | Statistics |

### Report Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/reports` | Yes | Create report |
| GET | `/reports/{id}` | Yes | Get report |
| GET | `/reports` | Yes | List reports |
| PUT | `/reports/{id}` | Yes | Update report |
| POST | `/reports/{id}/generate` | Yes | Generate report |
| POST | `/reports/{id}/complete` | Yes | Complete generation |
| GET | `/reports/{id}/download` | Yes | Download report |
| POST | `/reports/{id}/email` | Yes | Email report |
| DELETE | `/reports/{id}` | Yes | Delete report |

### Admin Endpoints
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/admin/dashboard` | Admin | Dashboard statistics |
| GET | `/admin/users` | Admin | List all users |
| DELETE | `/admin/users/{id}` | Admin | Delete user |
| POST | `/admin/users/{id}/activate` | Admin | Activate user |
| POST | `/admin/users/{id}/suspend` | Admin | Suspend user |
| POST | `/admin/maintenance/cleanup-sessions` | Admin | Cleanup sessions |
| POST | `/admin/maintenance/cleanup-reports` | Admin | Cleanup reports |
| GET | `/admin/system/health` | Admin | System health |

## Response Format

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "timestamp": "2024-01-01T00:00:00"
}
```

### Error Response
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid input data",
  "details": {
    "field": "email",
    "reason": "Invalid email format"
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

### Paginated Response
```json
{
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "has_next": true,
  "has_prev": false,
  "items": [ ... ]
}
```

## Security Features

### Authentication
- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt (12 rounds)
- Password strength validation
- Secure token expiration

### Authorization
- Role-based access control (RBAC)
- User/admin/moderator roles
- Resource-level access verification
- Admin-only endpoints

### Middleware
- CORS configuration for web clients
- Rate limiting (100 requests/minute default)
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- Request logging with IDs
- Request timing

### Data Protection
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- Soft deletes for data preservation
- Audit trail on all entities

## Performance Considerations

### Database
- Connection pooling for efficient resource usage
- Query optimization through proper indexing
- Lazy loading for relationships
- Batch operations where possible

### Caching
- Token payload caching
- Session state management
- Future: Redis integration for distributed caching

### Monitoring
- Request/response timing
- Error rate tracking
- Database query performance
- Health check endpoints for load balancers

## Integration Points

### Streamlit UI
- Compatible with existing session state
- API client for backend communication
- Token management in browser storage

### Future Extensions
- WebSocket support for real-time features
- GraphQL API alongside REST
- OpenAPI/Swagger documentation
- SDK generation for client languages
