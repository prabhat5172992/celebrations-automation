from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import schedule
import time
import threading
from datetime import datetime, timedelta
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
import os
from typing import List, Dict, Optional
from twilio.rest import Client

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect('celebrations.db')
    cursor = conn.cursor()
    
    # Create people table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            spouse_name TEXT,
            date TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('birthday', 'anniversary')),
            phone TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create wishes_sent table to track sent wishes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wishes_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER,
            sent_date TEXT,
            message TEXT,
            method TEXT,
            FOREIGN KEY (person_id) REFERENCES people (id)
        )
    ''')
    
    # Create message_templates table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            template TEXT NOT NULL,
            is_default BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Insert default message templates
    cursor.execute('''
        INSERT OR IGNORE INTO message_templates (type, template, is_default) VALUES
        ('birthday', '🎉 Happy Birthday {name}! 🎂 May your special day be filled with happiness, joy, and all your favorite things. Wishing you a fantastic year ahead filled with success and wonderful memories! 🌟', TRUE),
        ('anniversary', '💕 Happy Anniversary {name}! 🥂 May your love story continue to inspire others and may you both be blessed with many more years of togetherness, love, and happiness! 💍✨', TRUE)
    ''')
    
    conn.commit()
    conn.close()

class CelebrationManager:
    """Main class to handle celebration management"""
    
    def __init__(self):
        self.db_path = 'celebrations.db'
        init_db()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_person(self, name: str, date: str, person_type: str, 
                   spouse_name: str = None, phone: str = None, email: str = None) -> int:
        """Add a new person to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO people (name, spouse_name, date, type, phone, email)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, spouse_name, date, person_type, phone, email))
        
        person_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return person_id
    
    def get_all_people(self) -> List[Dict]:
        """Get all people from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM people ORDER BY date')
        rows = cursor.fetchall()
        
        people = []
        for row in rows:
            people.append({
                'id': row[0],
                'name': row[1],
                'spouse_name': row[2],
                'date': row[3],
                'type': row[4],
                'phone': row[5],
                'email': row[6],
                'created_at': row[7]
            })
        
        conn.close()
        return people
    
    def delete_person(self, person_id: int) -> bool:
        """Delete a person from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM people WHERE id = ?', (person_id,))
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        return rows_affected > 0
    
    def get_todays_celebrations(self) -> List[Dict]:
        """Get today's celebrations"""
        today = datetime.now().strftime('%m-%d')
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM people 
            WHERE strftime('%m-%d', date) = ?
        ''', (today,))
        
        rows = cursor.fetchall()
        celebrations = []
        for row in rows:
            celebrations.append({
                'id': row[0],
                'name': row[1],
                'spouse_name': row[2],
                'date': row[3],
                'type': row[4],
                'phone': row[5],
                'email': row[6]
            })
        
        conn.close()
        return celebrations
    
    def get_upcoming_celebrations(self, days: int = 30) -> List[Dict]:
        """Get upcoming celebrations within specified days"""
        people = self.get_all_people()
        today = datetime.now()
        upcoming = []
        
        for person in people:
            event_date = datetime.strptime(person['date'], '%Y-%m-%d')
            # Calculate this year's occurrence
            this_year_date = datetime(today.year, event_date.month, event_date.day)
            
            if this_year_date < today:
                # If already passed this year, check next year
                this_year_date = datetime(today.year + 1, event_date.month, event_date.day)
            
            days_until = (this_year_date - today).days
            
            if days_until <= days:
                person['days_until'] = days_until
                person['next_occurrence'] = this_year_date.strftime('%Y-%m-%d')
                upcoming.append(person)
        
        return sorted(upcoming, key=lambda x: x['days_until'])
    
    def generate_message(self, person: Dict) -> str:
        """Generate personalized message"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT template FROM message_templates 
            WHERE type = ? AND is_default = TRUE
        ''', (person['type'],))
        
        template = cursor.fetchone()
        conn.close()
        
        if template:
            if person['type'] == 'anniversary' and person['spouse_name']:
                name = f"{person['name']} & {person['spouse_name']}"
            else:
                name = person['name']
            
            return template[0].format(name=name)
        else:
            # Fallback messages
            if person['type'] == 'birthday':
                return f"🎉 Happy Birthday {person['name']}! Have a wonderful day! 🎂"
            else:
                name = f"{person['name']} & {person['spouse_name']}" if person['spouse_name'] else person['name']
                return f"💕 Happy Anniversary {name}! 🥂"
    
    def send_email_wish(self, person: Dict, message: str) -> bool:
        """Send email wish (HTML template-based)"""
        if not person['email']:
            return False

        try:
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('SENDER_EMAIL')
            sender_password = os.getenv('SENDER_PASSWORD')

            if not all([sender_email, sender_password]):
                print("Email configuration not found. Please set SMTP_SERVER, SENDER_EMAIL, and SENDER_PASSWORD environment variables.")
                return False

            # Create message object
            msg = MIMEMultipart('alternative')
            msg['From'] = sender_email
            msg['To'] = person['email']

            is_birthday = person['type'] == 'birthday'
            name = f"{person['name']} & {person['spouse_name']}" if person['spouse_name'] and not is_birthday else person['name']
            subject = f"🎉 Happy Birthday {name}!" if is_birthday else f"💕 Happy Anniversary {name}!"
            msg['Subject'] = subject

            # HTML Email Template
            html_template = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
                    <h2 style="color: {'#ff4081' if is_birthday else '#673ab7'}; text-align: center;">
                        {'🎂 Happy Birthday!' if is_birthday else '💍 Happy Anniversary!'}
                    </h2>
                    <p style="font-size: 16px; color: #333;">Dear <strong>{name}</strong>,</p>
                    <p style="font-size: 16px; color: #333;">{message}</p>
                    <p style="font-size: 16px; color: #333;">Wishing you joy, love, and wonderful memories! 🎊</p>
                    <hr style="margin: 30px 0;">
                    <p style="text-align: center; color: #888;">– With Love, from Celebration Reminder App</p>
                </div>
            </body>
            </html>
            """

            # Attach HTML content
            msg.attach(MIMEText(html_template, 'html'))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent to {person['name']} ({person['email']})")
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    
    def send_sms_wish(self, person: Dict, message: str) -> bool:
        """Send WhatsApp message via Twilio"""
        if not person['phone']:
            return False

        try:
            # Twilio credentials from environment
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER', 'whatsapp:+14155238886')  # default sandbox number
            to_whatsapp_number = f"whatsapp:{person['phone'].replace(' ', '').replace('-', '')}"

            if not all([account_sid, auth_token]):
                print("Twilio WhatsApp configuration missing. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
                return False

            client = Client(account_sid, auth_token)
            print(f"{person['name']} - Sending WhatsApp message to {to_whatsapp_number}, from {from_whatsapp_number}")

            # Send WhatsApp message
            message = client.messages.create(
                body=message,
                from_=from_whatsapp_number,
                to=to_whatsapp_number
            )

            print(f"✅ WhatsApp message sent to {person['name']} at {person['phone']}")
            return True

        except Exception as e:
            print(f"❌ Error sending WhatsApp message: {e}")
            return False
    
    def log_sent_wish(self, person_id: int, message: str, method: str):
        """Log sent wish to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO wishes_sent (person_id, sent_date, message, method)
            VALUES (?, ?, ?, ?)
        ''', (person_id, datetime.now().strftime('%Y-%m-%d'), message, method))
        
        conn.commit()
        conn.close()
    
    def send_wishes_for_today(self):
        """Send wishes for today's celebrations"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        print(f"📅 Running send_wishes_for_today() at {today_str}")

        celebrations = self.get_todays_celebrations()
        print(f"🎉 Found {len(celebrations)} celebrations today.")

        for person in celebrations:
            print(f"\n👤 Processing: {person['name']} (ID: {person['id']})")
            
            # Check if wish already sent today
            conn = self.get_connection()
            cursor = conn.cursor()
            # cursor.execute('''DELETE FROM wishes_sent WHERE sent_date = DATE('now') AND person_id = ?''', (person['id'],))

            cursor.execute('''
                SELECT COUNT(*) FROM wishes_sent 
                WHERE person_id = ? AND sent_date = ?
            ''', (person['id'], today_str))
            already_sent = cursor.fetchone()[0] > 0
            conn.close()

            if already_sent:
                print(f"🔁 Wish already sent to {person['name']}, but sending again for test.")

            # Generate personalized message
            message = self.generate_message(person)
            print(f"💬 Generated Message: {message}")

            sent = False

            # Send via email
            if person['email']:
                print(f"📧 Attempting email to: {person['email']}")
                if self.send_email_wish(person, message):
                    self.log_sent_wish(person['id'], message, 'email')
                    print(f"✅ Email sent to {person['name']} ({person['email']})")
                    sent = True
                else:
                    print(f"❌ Failed to send email to {person['name']}")

            # Send via WhatsApp
            if person['phone']:
                print(f"📲 Attempting WhatsApp to: {person['phone']}")
                if self.send_sms_wish(person, message):
                    self.log_sent_wish(person['id'], message, 'sms')
                    print(f"✅ WhatsApp message sent to {person['name']} ({person['phone']})")
                    sent = True
                else:
                    print(f"❌ Failed to send WhatsApp to {person['name']}")

            # Log in console if no contact method worked
            if not sent:
                print(f"📎 No successful delivery method for {person['name']}. Logging to console only.")
                self.log_sent_wish(person['id'], message, 'console')


# Initialize celebration manager
celebration_manager = CelebrationManager()

# API Routes
@app.route('/api/people', methods=['GET'])
def get_people():
    """Get all people"""
    try:
        people = celebration_manager.get_all_people()
        return jsonify({'success': True, 'data': people})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people', methods=['POST'])
def add_person():
    """Add a new person"""
    try:
        data = request.json
        person_id = celebration_manager.add_person(
            name=data['name'],
            date=data['date'],
            person_type=data['type'],
            spouse_name=data.get('spouse_name'),
            phone=data.get('phone'),
            email=data.get('email')
        )
        return jsonify({'success': True, 'id': person_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/people/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    """Delete a person"""
    try:
        success = celebration_manager.delete_person(person_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/today-celebrations', methods=['GET'])
def get_today_celebrations():
    """Get today's celebrations"""
    try:
        celebrations = celebration_manager.get_todays_celebrations()
        return jsonify({'success': True, 'data': celebrations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upcoming-celebrations', methods=['GET'])
def get_upcoming_celebrations():
    """Get upcoming celebrations"""
    try:
        days = request.args.get('days', 30, type=int)
        celebrations = celebration_manager.get_upcoming_celebrations(days)
        return jsonify({'success': True, 'data': celebrations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/send-wish/<int:person_id>', methods=['POST'])
def send_wish_now(person_id):
    """Send wish immediately"""
    try:
        conn = celebration_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM people WHERE id = ?', (person_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        person = {
            'id': row[0],
            'name': row[1],
            'spouse_name': row[2],
            'date': row[3],
            'type': row[4],
            'phone': row[5],
            'email': row[6]
        }
        
        message = celebration_manager.generate_message(person)
        
        # Send via available methods
        sent_methods = []
        if person['email']:
            if celebration_manager.send_email_wish(person, message):
                sent_methods.append('email')
                celebration_manager.log_sent_wish(person['id'], message, 'email')
        
        if person['phone']:
            if celebration_manager.send_sms_wish(person, message):
                sent_methods.append('sms')
                celebration_manager.log_sent_wish(person['id'], message, 'sms')
        
        if not sent_methods:
            celebration_manager.log_sent_wish(person['id'], message, 'manual')
            sent_methods.append('manual')
        
        return jsonify({
            'success': True, 
            'message': message,
            'sent_via': sent_methods
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/message-preview/<int:person_id>', methods=['GET'])
def get_message_preview(person_id):
    """Get message preview for a person"""
    try:
        conn = celebration_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM people WHERE id = ?', (person_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Person not found'}), 404
        
        person = {
            'id': row[0],
            'name': row[1],
            'spouse_name': row[2],
            'date': row[3],
            'type': row[4],
            'phone': row[5],
            'email': row[6]
        }
        
        message = celebration_manager.generate_message(person)
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Scheduler functions
def schedule_daily_wishes(test_mode=False):
    """Schedule daily wish sending"""

    def safe_send_wishes():
        try:
            print("🎉 Triggering send_wishes_for_today...")
            celebration_manager.send_wishes_for_today()
            print("✅ Wishes sent successfully.")
        except Exception as e:
            print("❌ Error while sending wishes:", e)

    def run_scheduler():
        IST = pytz.timezone("Asia/Kolkata")

        if test_mode:
            print("🔧 Test mode enabled: running every 1 minute")
            schedule.every(1).minutes.do(safe_send_wishes)
        else:
            schedule_time = "09:00"
            print(f"📅 Scheduling wish sending at {schedule_time} IST daily")
            schedule.every().day.at(schedule_time).do(safe_send_wishes)

        print("🕒 Scheduler started. IST time:",
              datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"))

        while True:
            now_ist = datetime.now(IST)
            print("⏰ Checking scheduler at IST time:",
                  now_ist.strftime("%Y-%m-%d %H:%M:%S"))
            schedule.run_pending()
            time.sleep(60)

    # Prevent duplicate thread creation
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

# Database initialization and sample data
def add_sample_data():
    """Add sample data for testing"""
    try:
        # Check if data already exists
        people = celebration_manager.get_all_people()
        if len(people) > 0:
            return
        
        # Add sample people
        celebration_manager.add_person(
            name="Prabhat Ranjan",
            date="1996-06-22",
            person_type="birthday",
            phone="+91-8867412196",
            email="prabhat5172992@gmail.com"
        )
        
        celebration_manager.add_person(
            name="Mamta Gola",
            date="2022-05-12",
            person_type="anniversary",
            spouse_name="Prabhat Ranjan",
            phone="+91-7300645940",
            email="mamta1998gola@gmail.com"
        )
        
        celebration_manager.add_person(
            name="Deepshikha",
            date=f"2002-11-28",
            person_type="birthday",
            phone="+91-7667961613",
            email="prabhat7660403@gmail.com"
        )
        
        print("Sample data added successfully!")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected'
    })

if __name__ == '__main__':
    print("🎉 Starting Celebration Reminder Backend...")
    
    # # Initialize database and add sample data
    # add_sample_data()
    
    # # Start the scheduler
    # schedule_daily_wishes()
    from werkzeug.serving import is_running_from_reloader

    if not is_running_from_reloader():
        print("✅ Starting scheduler only in main process...")
        add_sample_data()
        schedule_daily_wishes()
    
    print("📅 Daily wish scheduler started (sends wishes at 9:00 AM)")
    print("🚀 Server running on http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/people - Get all people")
    print("  POST /api/people - Add new person")
    print("  DELETE /api/people/<id> - Delete person")
    print("  GET  /api/today-celebrations - Get today's celebrations")
    print("  GET  /api/upcoming-celebrations - Get upcoming celebrations")
    print("  POST /api/send-wish/<id> - Send wish immediately")
    print("  GET  /api/message-preview/<id> - Preview message")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)