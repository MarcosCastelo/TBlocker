import os
import time
import psutil
import time
import getpass
import signal
import atexit
import sys
from datetime import datetime

from utils import load_config

HOST_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"
LOG_FILE = "blocker.log"

sites = []
schedule = {}
hardcore = False

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log:
        message = f"[{timestamp}] {message}\n"
        log.write(message)
        print(message)

def is_within_schedule(schedule):
    """Check if now is in schedule"""
    if not schedule:
        return True
    try:
        now = datetime.now().time()
        start = datetime.strptime(schedule["start"], "%H:%M").time()
        end = datetime.strptime(schedule["end"], "%H:%M").time()
        
        if start <= end:
            return start <= now <= end
        else:
            return now >= start or now <= end
    except Exception as e:
        log_event(f"Schedule verification error: {e}")
        
def has_block_time_ended(schedule):
    if not schedule:
        return True
    now = datetime.now().time()
    end = datetime.strptime(schedule["end"], "%H:%M").time()
    if schedule["start"] <= schedule["end"]:
        return now > end
    else:
        return now > end and now < datetime.strptime(schedule["start"], "%H:%M").time()

def block_sites(sites):
    with open(HOST_PATH, "r+") as file:
        content = file.read()
        for site in sites:
            entry = f"{REDIRECT_IP} {site}\n"
            if site not in content:
                file.write(entry)

def unblock_sites(sites):
    with open(HOST_PATH, "r") as file:
        lines = file.readlines()

    with open(HOST_PATH, "w") as file:
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 2 and parts[0] == REDIRECT_IP and parts[1] in sites:
                continue 
            file.write(line)

def kill_blocked_apps(apps):
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() in apps:
                proc.kill()
                log_event(f"[BLOCKED] {proc.info["name"]}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("Invalid Config: is not a dict")
    if "blocked_sites" in config and not isinstance(config["blocked_sites"], list):
        raise ValueError("'bocked_sites' must be a list.")
    if "blocked_apps" in config and not isinstance(config["blocked_apps"], list):
        raise ValueError("'bocked_apps' must be a list.")
    if "schedule" in config:
        s = config["schedule"]
        if not ("start" in s and "end" in s):
            raise ValueError("'schedule' must contain 'start' and 'end'")

def verify_password(stored_password):
    attempts = 3
    while attempts > 0:
        typed = getpass.getpass("Type the password: ")
        if typed == stored_password:
            log_event("[✔] Senha correta. Bloqueador encerrado.")
            return True
        else:
            print("[X] Senha incorreta.")
            attempts -= 1
    log_event("[!] Tentativas esgotadas. Continuando bloqueio.")
    return False

def clean_exit():
    log_event("[EXIT] Ending process")
    if not hardcore or has_block_time_ended(schedule):
        unblock_sites(sites)
        log_event("[TBlocker] All released.")
    else:
        log_event("[Hardcore Mode] Block still alive.")

def main():
    global sites, schedule, hardcore
    
    try:
        config = load_config()
        validate_config(config)
    except Exception as e:
        log_event(f"[ERROR] Failed to load config: {e}")
        
    sites = config["blocked_sites"]
    apps = [app.lower() for app in config.get("blocked_apps", [])]
    schedule = config.get("schedule")
    password = config.get("unlock_password")
    hardcore = config.get("hardcore", False)
    
    log_event("[TBlocker] running... (CTRL+C - close)")
    
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    atexit.register(clean_exit)
    
    try:
        while True:
            if is_within_schedule(schedule):    
                block_sites(sites)
                kill_blocked_apps(apps)
            time.sleep(5)
    except SystemExit:
        pass
    
if __name__ == "__main__":
    main()