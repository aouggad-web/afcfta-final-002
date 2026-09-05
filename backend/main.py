# ASGI entry point — delegates to server.py so both work:
#   uvicorn backend.server:app
#   uvicorn backend.main:app
from server import app  # noqa: F401
