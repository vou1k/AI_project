#!/usr/bin/env python3
"""
Main runner script for AI Test Platform
Starts both backend and demo application
"""

import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def run_backend():
    """Start backend server"""
    print("🚀 Starting backend at http://localhost:8000")
    os.chdir("backend")
    subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"])

def run_demo_app():
    """Start demo application"""
    print("📱 Starting demo app at http://localhost:5000")
    os.chdir("demo_app")
    subprocess.run([sys.executable, "app.py"])

def main():
    print("=" * 60)
    print("🤖 AI Test Platform - Starting all components")
    print("=" * 60)
    
    # Create necessary directories
    os.makedirs("tests", exist_ok=True)
    
    # Get current directory
    root_dir = os.getcwd()
    
    # Start backend in separate thread
    def run_backend_thread():
        os.chdir(root_dir)
        run_backend()
    
    # Start demo app in separate thread
    def run_demo_thread():
        os.chdir(root_dir)
        run_demo_app()
    
    backend_thread = Thread(target=run_backend_thread)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Give backend time to start
    time.sleep(2)
    
    demo_thread = Thread(target=run_demo_thread)
    demo_thread.daemon = True
    demo_thread.start()
    
    # Give demo app time to start
    time.sleep(2)
    
    # Open browser
    print("\n🌐 Opening interface in browser...")
    webbrowser.open("http://localhost:8000")
    
    print("\n✅ All components started!")
    print("📊 Interface: http://localhost:8000")
    print("🔧 Demo API: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Stopping...")
        sys.exit(0)

if __name__ == "__main__":
    main()