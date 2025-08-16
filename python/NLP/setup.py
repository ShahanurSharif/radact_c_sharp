#!/usr/bin/env python3
"""
Setup script for Azure AI Foundry Document Redaction
Run this script to install dependencies and configure the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version check passed: {version.major}.{version.minor}.{version.micro}")
    return True

def setup_virtual_environment():
    """Setup virtual environment if it doesn't exist"""
    parent_dir = Path(__file__).parent.parent
    venv_path = parent_dir / "venv"
    
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        if not run_command(f"python3 -m venv {venv_path}", "Virtual environment creation"):
            return False
    else:
        print("✅ Virtual environment already exists")
    
    return True

def install_dependencies():
    """Install required Python packages"""
    parent_dir = Path(__file__).parent.parent
    venv_python = parent_dir / "venv" / "bin" / "python"
    
    # Install base requirements
    base_requirements = parent_dir / "requirements.txt"
    if base_requirements.exists():
        if not run_command(f"{venv_python} -m pip install -r {base_requirements}", 
                          "Installing base requirements"):
            return False
    
    # Install NLP-specific requirements
    nlp_requirements = Path(__file__).parent / "requirements.txt"
    if nlp_requirements.exists():
        if not run_command(f"{venv_python} -m pip install -r {nlp_requirements}", 
                          "Installing NLP requirements"):
            return False
    
    return True

def create_config_files():
    """Create configuration files if they don't exist"""
    current_dir = Path(__file__).parent
    
    # Create .env file from template if it doesn't exist
    env_file = current_dir / ".env"
    env_template = current_dir / ".env.template"
    
    if not env_file.exists() and env_template.exists():
        import shutil
        shutil.copy(env_template, env_file)
        print("✅ Created .env configuration file")
        print("📝 Please edit .env file with your Azure credentials")
    elif env_file.exists():
        print("✅ Configuration file already exists")
    else:
        print("⚠️  No configuration template found")
    
    return True

def verify_installation():
    """Verify that the installation is working"""
    parent_dir = Path(__file__).parent.parent
    venv_python = parent_dir / "venv" / "bin" / "python"
    
    test_command = f'{venv_python} -c "import azure.ai.textanalytics; print(\'Azure AI Text Analytics imported successfully\')"'
    
    return run_command(test_command, "Verifying Azure AI installation")

def main():
    """Main setup function"""
    print("🚀 Azure AI Foundry Document Redaction Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Setup virtual environment
    if not setup_virtual_environment():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create configuration files
    if not create_config_files():
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        print("⚠️  Installation completed but verification failed")
        print("This might be due to missing Azure credentials")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit the .env file with your Azure credentials")
    print("2. Activate the virtual environment:")
    print("   source ../venv/bin/activate")
    print("3. Test the installation:")
    print("   python main.py config")
    print("   python main.py analyze ../docs/1.docx")

if __name__ == "__main__":
    main()
