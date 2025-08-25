# Microservices Template

## Background

The backend development is a complex process. It involves a lot of components and services. This is a template for a microservice built with Python and Django Ninja with the support of the Devcontainers.

## Features

This template includes the following features:

- It supports the Devcontainers;
- It made with django ninja;
- It supports the authentication with JWT;
- It's already configured for the full support of the environment variables;
- It's already configured for Swagger UI;

## Structure

The project follows a structured approach to separate concerns, making it easier to maintain and scale. Here's a breakdown of the key directories inside `app/app`:

- **`common/`**: Contains shared utilities, base classes (like `BaseModel`), custom exceptions, global constants, parsers, and security configurations. This is for code that is used across different parts of the application.

- **`endpoints/`**: Holds the core business logic for your API endpoints. Each feature or model should have its own file (e.g., `custom_user.py`). These files contain functions that are called by the routes.

- **`management/commands/`**: For custom Django management commands (e.g., `python manage.py create_user`).

- **`middlewares/`**: Contains custom middleware for processing requests and responses. The `pipeline.py` helps in orchestrating middleware chains.

- **`models/`**: Defines the Django ORM models, which represent your database tables.

- **`routes/`**: This is where API routing is defined using Django Ninja.
    - `routes/v1/`: Contains routers for version 1 of the API. Each feature should have its own router file (e.g., `custom_user.py`). These files define the URL paths, HTTP methods, and connect them to the endpoint logic in the `endpoints/` directory.
    - `routes.py`: The main API router that aggregates all the versioned routers.

- **`schemas/`**: Pydantic schemas are defined here for request and response data validation. This ensures that the data flowing in and out of your API is in the correct format.
    - `req/`: Schemas for incoming request bodies.
    - `res/`: Schemas for outgoing response bodies.

- **`services/`**: Contains business logic that is independent of the web layer. For example, a `CustomUserService` might handle JWT token generation and verification.

## How to Create a New Endpoint

Let's walk through creating a new set of endpoints for a hypothetical `Post` model.

### 1. Create the Model

First, define the `Post` model in a new file `app/app/models/post.py`:

```python
# app/app/models/post.py
from app.common.default.models import BaseModel
from .custom_user import CustomUser

class Post(BaseModel):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
```

Then you need to add the model to the `app/app/models/__init__.py` file.

```python
# app/app/models/__init__.py
from .post import Post
from .custom_user import CustomUser

__all__ = [
    "CustomUser",
    "Post"
]


```

Remember to create and run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Create Schemas

Next, define the request and response schemas in `app/app/schemas/req/post.py` and `app/app/schemas/res/post.py`.

Request schema (`app/app/schemas/req/post.py`):
```python
# app/app/schemas/req/post.py
from ninja import Schema

class PostRequest(Schema):
    title: str
    content: str
```

Response schema (`app/app/schemas/res/post.py`):
```python
# app/app/schemas/res/post.py
from ninja import Schema
from datetime import datetime

class PostResponse(Schema):
    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    updated_at: datetime
```

### 3. Create Endpoint Logic

Now, create the business logic for the endpoints in `app/app/endpoints/v1/post.py`.

```python
# app/app/endpoints/v1/post.py
from django.http import HttpRequest
from app.common.default.types import EndPointResponse
from app.common.default.standard_response import standard_response
from app.models.post import Post
from app.schemas.req.post import PostRequest
from app.schemas.res.post import PostResponse
from app.common.default.utils import get_user_from_request

def create_post_ep(request: HttpRequest, data: PostRequest) -> EndPointResponse:
    user = get_user_from_request(request)
    post = Post.objects.create(
        title=data.title,
        content=data.content,
        author=user
    )
    response_data = PostResponse.from_orm(post)
    return standard_response(status_code=201, message="Post created successfully", data=response_data)

def get_posts_ep(request: HttpRequest) -> EndPointResponse:
    posts = Post.objects.all()
    response_data = [PostResponse.from_orm(post) for post in posts]
    return standard_response(status_code=200, message="Posts retrieved successfully", data=response_data)
```

### 4. Create the Router

Define the API routes in `app/app/routes/v1/post.py`. This file connects the HTTP paths to your endpoint logic.

```python
# app/app/routes/v1/post.py
from ninja import Router
from django.http import HttpRequest
from app.common.default.standard_response import StandardResponse
from app.schemas.req.post import PostRequest
from app.schemas.res.post import PostResponse
from app.common.default.responses import responses
from app.common.default.security import JWTAuth
from app.middlewares.default.pipeline import pipeline
from app.endpoints.v1.post import create_post_ep, get_posts_ep

v1 = Router(tags=["Posts"])

@v1.post("", response=responses({201: StandardResponse[PostResponse]}), auth=JWTAuth())
def create_post(request: HttpRequest, data: PostRequest):
    return pipeline(request, endpoint=create_post_ep, data=data)

@v1.get("", response=responses({200: StandardResponse[list[PostResponse]]}))
def get_posts(request: HttpRequest):
    return pipeline(request, endpoint=get_posts_ep)
```

### 5. Register the New Router

Finally, register your new `post` router in the main API router file, `app/app/routes/routes.py`.

```python
# app/app/routes/routes.py
# ... other imports
from app.routes.v1.custom_user import v1 as custom_user_router
from app.routes.v1.post import v1 as post_router # Import the new router

v1 = NinjaAPI(
    version="1.0.0", title="Template API", docs_url="/docs/v1", parser=ORJSONParser()
)

v1.add_router("v1/operator", custom_user_router)
v1.add_router("v1/posts", post_router) # Add the new router

# ... exception handlers ...
```

Now you can start the server, go to `/api/docs/v1`, and you will see your new "Posts" endpoints.

