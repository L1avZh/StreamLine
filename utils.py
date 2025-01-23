import json
import socket
import random
import logging

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

def colored(text, color):
    color_map = {
        'red': Colors.RED,
        'green': Colors.GREEN,
        'yellow': Colors.YELLOW,
        'blue': Colors.BLUE,
        'magenta': Colors.MAGENTA,
        'cyan': Colors.CYAN
    }
    return f"{color_map.get(color, Colors.RESET)}{text}{Colors.RESET}"

def print_banner():
    banner = [
        colored(r" ___ _                      _    _          ", "cyan"),
        colored(r"/ __| |_ _ _ ___ __ _ _ __ | |  (_)_ _  ___ ", "green"),
        colored(r"\__ \  _| '_/ -_) _` | '  \| |__| | ' \/ -_)", "yellow"),
        colored(r"|___/\__|_| \___\__,_|_|_|_|____|_|_||_\___|", "red"),
        colored("\n         - Made by L1avZh\n", "magenta")
    ]
    print("\n".join(banner))

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def load_config(filename="config.json"):
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
            config['port'] = int(config.get('port') or find_free_port())
            return config
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        logging.error("Config file not found or invalid. Using defaults.")
        return {'host': '127.0.0.1', 'port': find_free_port()}
