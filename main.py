from threading import Thread
from web import start_web
from bot import run_bot_once

if __name__ == "__main__":
    Thread(target=start_web).start()  # Start web server
    # UptimeRobot or browser will ping /ping endpoint