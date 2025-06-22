#!/usr/bin/env python3
"""
Celebration Reminder App Setup Script
This script helps you set up the birthday and anniversary reminder application.
"""

import os
import sys
import subprocess
import sqlite3
from datetime import datetime

def print_header():
    print("🎉" + "="*60 + "🎉")
    print("     CELEBRATION REMINDER APP SETUP")
    print("🎂" + "="*60 + "💕")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python version: {sys.version.split()[0]}")

def install_requirements():
    """Install required Python packages"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies!")
        print("Please run: pip install -r requirements.txt")
        return False
    return True

def setup_database():
    """Initialize the SQLite database"""
    print("\n🗃️  Setting up database...")
    try:
        # Import after dependencies are installed
        from app import init_db, CelebrationManager
        
        init_db()
        print("✅ Database initialized successfully!")
        
        # Add sample data
        manager = CelebrationManager()
        
        # Check if sample data already exists
        people = manager.get_all_people()
        if len(people) == 0:
            print("📝 Adding sample data...")
            
            # Add sample birthday
            manager.add_person(
                name="Prabhat Ranjan",
                date="1996-06-22",
                person_type="birthday",
                phone="+918867412196",
                email="prabhat5172992@gmail.com"
            )
            
            # Add sample anniversary
            manager.add_person(
                name="Mamta Gola",
                date="2022-05-12",
                person_type="anniversary",
                spouse_name="Prabhat Ranjan",
                phone="+91-7300645940",
                email="mamta1998gola@gmail.com"
            )
            
            # Add today's birthday for testing
            today = datetime.now().strftime("%Y-%m-%d")
            manager.add_person(
                name="Deepshikha",
                date=f"2002-11-28",
                person_type="birthday",
                phone="+91-7667961613",
                email="prabhat7660403@gmail.com"
            )
            
            print("✅ Sample data added!")
        else:
            print("✅ Database already contains data!")
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    return True

def create_env_file():
    """Create environment configuration file"""
    print("\n⚙️  Setting up environment configuration...")
    
    if os.path.exists('.env'):
        print("✅ .env file already exists!")
        return
    
    # Copy from example
    if os.path.exists('.env.example'):
        try:
            with open('.env.example', 'r') as example:
                with open('.env', 'w') as env:
                    env.write(example.read())
            print("✅ .env file created from example!")
            print("📝 Please edit .env file with your email/SMS credentials")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    else:
        # Create basic .env file
        env_content = """# Email Configuration (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# SMS Configuration (Optional)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# App Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
"""
        try:
            with open('.env', 'w') as f:
                f.write(env_content)
            print("✅ .env file created!")
            print("📝 Please edit .env file with your credentials")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")

def create_startup_scripts():
    """Create startup scripts for easy launching"""
    print("\n🚀 Creating startup scripts...")
    
    # Windows batch script
    windows_script = """@echo off
echo Starting Celebration Reminder App...
echo Backend: http://localhost:5000
echo.
python app.py
pause
"""
    
    # Linux/Mac shell script
    unix_script = """#!/bin/bash
echo "🎉 Starting Celebration Reminder App..."
echo "Backend: http://localhost:5000"
echo ""
python3 app.py
"""
    
    try:
        with open('start_app.bat', 'w') as f:
            f.write(windows_script)
        
        with open('start_app.sh', 'w') as f:
            f.write(unix_script)
        
        # Make shell script executable on Unix systems
        if os.name != 'nt':
            os.chmod('start_app.sh', 0o755)
        
        print("✅ Startup scripts created!")
        print("   Windows: start_app.bat")
        print("   Linux/Mac: ./start_app.sh")
        
    except Exception as e:
        print(f"❌ Failed to create startup scripts: {e}")

def print_instructions():
    """Print final setup instructions"""
    print("\n" + "="*60)
    print("🎊 SETUP COMPLETED SUCCESSFULLY! 🎊")
    print("="*60)
    print()
    print("📋 NEXT STEPS:")
    print()
    print("1. 📧 Configure Email (Optional):")
    print("   - Edit .env file with your Gmail credentials")
    print("   - Use App Password for Gmail (not regular password)")
    print()
    print("2. 📱 Configure SMS (Optional):")
    print("   - Sign up for Twilio account")
    print("   - Add Twilio credentials to .env file")
    print()
    print("3. 🚀 Start the Application:")
    print("   - Windows: double-click start_app.bat")
    print("   - Linux/Mac: ./start_app.sh")
    print("   - Or manually: python app.py")
    print()
    print("4. 🌐 Access the App:")
    print("   - Backend API: http://localhost:5000")
    print("   - Frontend: Open the React app in your browser")
    print()
    print("📁 FILES CREATED:")
    print("   - celebrations.db (SQLite database)")
    print("   - .env (configuration file)")
    print("   - start_app.bat/.sh (startup scripts)")
    print()
    print("🎯 FEATURES:")
    print("   ✅ Add birthdays and anniversaries")
    print("   ✅ Automatic daily wish sending")
    print("   ✅ Email and SMS notifications")
    print("   ✅ Customizable messages")
    print("   ✅ Multiple events per day support")
    print()
    print("📞 SUPPORT:")
    print("   - Check logs for any errors")
    print("   - Ensure .env file is properly configured")
    print("   - Test with sample data provided")
    print()
    print("🎉 HAPPY CELEBRATING! 🎉")

def main():
    """Main setup function"""
    print_header()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    if not install_requirements():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Create environment file
    create_env_file()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Print final instructions
    print_instructions()

if __name__ == "__main__":
    main()