from flask import Flask, render_template_string
from datetime import datetime
from bot import run_bot_once

app = Flask(__name__)
bot_status = {
    "active_matches": [],
    "last_check": "Not yet run"
}

@app.route('/')
def index():
    html = """
    <html>
    <head><title>Live Betting Tracker</title></head>
    <body>
        <h2>⚽ 36’ & 80’ Betting Strategy Tracker</h2>
        <p><b>Last Checked:</b> {{ last_check }}</p>
        <ul>
        {% for match in active_matches %}
            <li>{{ match }}</li>
        {% else %}
            <li>No active matches right now.</li>
        {% endfor %}
        </ul>
    </body>
    </html>
    """
    return render_template_string(html, **bot_status)

@app.route('/ping')
def ping():
    run_bot_once()
    return f"✅ Bot triggered at {datetime.now().strftime('%H:%M:%S')}", 200

def start_web():
    app.run(host='0.0.0.0', port=8080)