from flask import Flask, request
from collections import OrderedDict, deque
import schedule
import time
import threading

app = Flask(__name__)

MAX_RPM = 5  # Maximum requests per minute, adjust as needed
CLEAN_INTERVAL = 60  # Interval to clean the log in seconds

log = OrderedDict()
log_lock = threading.Lock()

@app.before_request
def rate_limit():
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    with log_lock:
        if ip in log:
            while log[ip] and time.time() - log[ip][0] > 60:
                log[ip].popleft()
            if len(log[ip]) < MAX_RPM:
                log[ip].append(time.time())

            else:
                return "Too many requests. Please try again later.", 429
        else:
            log[ip] = deque(maxlen=MAX_RPM)
            log[ip].append(time.time())

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    schedule.every(CLEAN_INTERVAL).seconds.do(clean_log)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

def clean_log():
    with log_lock:
        to_delete = list()
        for ip in reversed(log):
            if time.time() - log[ip][-1] > 60:
                to_delete.append(ip)
            else:
                break
        for ip in to_delete:
            del log[ip]
        del to_delete

@app.route('/test')
def home():
    print("Endpoint accessed by IP:", request.remote_addr, " with ", len(log[request.remote_addr]), " requests in the last minute.")
    return "Welcome to the rate-limited API!", 200

start_scheduler()