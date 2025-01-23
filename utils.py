import json
import ssl
import random
import socket

def colored(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, colors['reset'])}{text}{colors['reset']}"

def print_banner():
    banner = [
        colored(r" ___ _                      _    _          ", "cyan"),
        colored(r"/ __| |_ _ _ ___ __ _ _ __ | |  (_)_ _  ___ ", "green"),
        colored(r"\__ \  _| '_/ -_) _` | '  \| |__| | ' \/ -_)", "yellow"),
        colored(r"|___/\__|_| \___\__,_|_|_|_|____|_|_||_\___|", "red"),
        colored("\n         -Made by L1avZh\n", "magenta")
    ]
    print("\n".join(banner))

def load_config(filename="config.json"):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'host': '127.0.0.1', 'port': 5000}

def secure_socket(sock):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="certs/cert.pem", keyfile="certs/key.pem")
        return context.wrap_socket(sock, server_side=True)
    except FileNotFoundError:
        return sock

def find_free_port():
    while True:
        port = random.randint(49152, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue
