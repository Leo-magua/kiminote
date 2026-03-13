#!/usr/bin/env python3
"""
AI Notes - Startup Script
"""
import sys
import uvicorn
from app.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    print(f"📝 AI Notes starting on http://{HOST}:{PORT}")
    print(f"📁 Data directory: ./data")
    print(f"🤖 AI features: {'enabled' if DEBUG else 'check .env config'}")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info"
    )
