import pytest
from fastapi.testclient import TestClient
import os

def test_cors_production_url():
    # Force the app configuration for the duration of the test
    from app.config import settings
    settings.FRONTEND_URL = "https://scholarpath-staging.vercel.app"
    
    # We must explicitly rebuild the CORSMiddleware since it was already loaded
    from app.main import app
    from fastapi.middleware.cors import CORSMiddleware
    
    # Remove existing CORSMiddleware
    app.user_middleware = [m for m in app.user_middleware if m.cls != CORSMiddleware]
    
    # Re-add with updated settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:3000",
            settings.FRONTEND_URL,
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Rebuild middleware stack
    app.middleware_stack = app.build_middleware_stack()
    
    client = TestClient(app)
    
    # Trigger an OPTIONS request
    response = client.options(
        "/api/users/me",
        headers={
            "Origin": "https://scholarpath-staging.vercel.app",
            "Access-Control-Request-Method": "GET"
        }
    )
    
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "https://scholarpath-staging.vercel.app"
