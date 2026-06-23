from fastapi import FastAPI
import uvicorn

tags_metadata = [
    {
        "name": "System",
        "description": "System APIs",
    },
    {
        "name": "Users",
        "description": "User management APIs",
    },
]

app = FastAPI(
    title="Music Backend API",
    description="API Documentation for Music Backend",
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/swagger",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,
        "docExpansion": "list",
        "displayRequestDuration": True,
    },
)

@app.get(
    "/",
    tags=["System"],
    summary="Health Check",
    description="Check API status",
)
def root():
    return {"message": "Hello World"}

@app.get(
    "/users/{user_id}",
    tags=["Users"],
    summary="Get User",
    description="Get user information by ID",
)
def get_user(user_id: int):
    return {
        "id": user_id,
        "name": "Vu"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
    )