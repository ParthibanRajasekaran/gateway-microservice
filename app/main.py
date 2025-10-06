from fastapi import FastAPI
from .api.routes import router
from .core.logging import configure_logging

configure_logging()
app = FastAPI(title="Price Calculator Service", version="1.0.0")
app.include_router(router)
