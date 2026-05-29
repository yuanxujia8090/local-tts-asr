#!/usr/bin/env python3
"""Start the Qwen3 Voice Service server."""

import uvicorn
from src.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        # Exclude virtual env and cache from file watching
        reload_excludes=[
            "*.pyc",
            "__pycache__",
            ".venv/**",
        ],
    )
