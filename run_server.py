#!/usr/bin/env python3
"""
Startup script for Spine Industry Scraper Flask Server
"""

import os
import sys
import subprocess

def main():
    """Start the Flask server with proper environment"""
    print("🦴 Starting Spine Industry Scraper Server...")
    print("=" * 50)

    # Change to server directory
    server_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(server_dir)

    # Check if virtual environment exists
    venv_path = os.path.join(server_dir, 'venv')
    if os.path.exists(venv_path):
        print("✅ Virtual environment found")
        # Activate virtual environment
        if os.name == 'nt':  # Windows
            activate_script = os.path.join(venv_path, 'Scripts', 'activate.bat')
            python_path = os.path.join(venv_path, 'Scripts', 'python.exe')
        else:  # Unix/Linux
            activate_script = os.path.join(venv_path, 'bin', 'activate')
            python_path = os.path.join(venv_path, 'bin', 'python')

        if os.path.exists(python_path):
            print("🚀 Starting server with virtual environment...")
            os.system(f'"{python_path}" app.py')
        else:
            print("❌ Virtual environment Python not found")
            print("🔧 Creating virtual environment...")
            create_venv()
    else:
        print("📦 Virtual environment not found")
        print("🔧 Creating virtual environment...")
        create_venv()

def create_venv():
    """Create virtual environment and install dependencies"""
    server_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(server_dir)

    print("📦 Creating virtual environment...")
    subprocess.run([sys.executable, '-m', 'venv', 'venv'])

    print("📥 Installing dependencies...")
    if os.name == 'nt':  # Windows
        pip_path = os.path.join('venv', 'Scripts', 'pip.exe')
    else:  # Unix/Linux
        pip_path = os.path.join('venv', 'bin', 'pip')

    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'])

    print("✅ Setup complete!")
    print("🚀 Starting server...")
    os.system('python app.py')

if __name__ == "__main__":
    main()