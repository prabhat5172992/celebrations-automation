# 🎉 Celebration Automation App

An automated birthday and anniversary celebration app built using **Flask (Python)** for the backend and **React + Vite + Tailwind + TypeScript** for the frontend.

This app automatically sends **email** and **WhatsApp wishes** daily at a scheduled time, with personalized messages using stored templates. It also provides a dashboard to view, add, or delete upcoming and today's celebrations.

---

## 📦 Features

- 🎂 Auto-sends birthday and anniversary wishes via Email and WhatsApp
- 🧠 Personalized message generation with customizable templates
- 🗓 Scheduler (Python + `schedule`) runs daily at a specified IST time
- 🧾 Logs sent wishes to prevent duplicates
- 📧 HTML email support
- 💬 WhatsApp message support using **Twilio**
- 🧑‍💻 REST API to manage people, preview messages, and trigger wishes
- 🌐 Modern frontend with React + Tailwind for a clean UI

---

## 🏗 Tech Stack

**Backend:**
- Python 3.x
- Flask + Flask-CORS
- SQLite
- schedule
- smtplib (for email)
- Twilio (for WhatsApp)

**Frontend:**
- React (with Vite)
- TypeScript
- Tailwind CSS

---

## 🚀 Setup

### 🔧 Backend (Flask)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

# Set environment variables (create a .env file or export manually)
```
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SENDER_EMAIL=your_email@gmail.com
export SENDER_PASSWORD=your_password
export TWILIO_ACCOUNT_SID=your_sid
export TWILIO_AUTH_TOKEN=your_token
export TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886  # Default sandbox
```

# Run the app
```
python app.py
```

### 🧪 Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

---

## 📅 Scheduler

The scheduler is automatically started when the Flask app launches and runs daily at \`23:01 IST\` (or custom time if configured). It finds all people whose celebration date matches today and sends the appropriate message.

---

## 📬 API Endpoints

| Method | Endpoint                         | Description                             |
|--------|----------------------------------|-----------------------------------------|
| GET    | \`/api/health\`                    | Health check                            |
| GET    | \`/api/people\`                    | Get all people                          |
| POST   | \`/api/people\`                    | Add new person                          |
| DELETE | \`/api/people/<id>\`              | Delete person                           |
| GET    | \`/api/today-celebrations\`        | Get today's celebrations                |
| GET    | \`/api/upcoming-celebrations?days=30\` | Get upcoming events                   |
| POST   | \`/api/send-wish/<id>\`           | Trigger wish manually                   |
| GET    | \`/api/message-preview/<id>\`     | Get preview of message for a person     |

---

## 🔐 Environment Variables

| Variable               | Required | Description                            |
|------------------------|----------|----------------------------------------|
| \`SMTP_SERVER\`          | ✅       | Email SMTP server (e.g., smtp.gmail.com) |
| \`SMTP_PORT\`            | ✅       | Email SMTP port (e.g., 587)             |
| \`SENDER_EMAIL\`         | ✅       | Sender email address                    |
| \`SENDER_PASSWORD\`      | ✅       | Sender email password/app password      |
| \`TWILIO_ACCOUNT_SID\`   | ✅       | Twilio SID for WhatsApp                 |
| \`TWILIO_AUTH_TOKEN\`    | ✅       | Twilio Auth token                       |
| \`TWILIO_WHATSAPP_NUMBER\` | ✅     | Twilio WhatsApp sender (e.g. \`whatsapp:+14155238886\`) |

---

## 🧪 Sample Data

On first run, the app populates the database with sample people for testing.

---

## 📂 Folder Structure

```
project-root/
│
├── backend/
│   ├── app.py
│   ├── celebrations.db
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── vite.config.ts
│   └── ...
│
├── .gitignore
└── README.md
```

---

## 📜 License

MIT License – feel free to use, modify, and share.

---

## 👨‍💻 Author

**Prabhat Ranjan**  
Crafted with ❤️ using Python, Flask, and React

---