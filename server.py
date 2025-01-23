import socket
import threading
import sys
import random
import json
import logging
import ssl
import re
from concurrent.futures import ThreadPoolExecutor

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
    """Simulate colored output using ANSI escape codes."""
    color_map = {
        'red': Colors.RED,
        'green': Colors.GREEN,
        'yellow': Colors.YELLOW,
        'blue': Colors.BLUE,
        'magenta': Colors.MAGENTA,
        'cyan': Colors.CYAN
    }
    return f"{color_map.get(color, Colors.RESET)}{text}{Colors.RESET}"

def find_free_port():
    """Find an available port dynamically."""
    while True:
        port = random.randint(49152, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                continue

def load_config(filename="config.json"):
    """Load configuration from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'host': '0.0.0.0', 'port': None}

def secure_socket(sock):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
        return context.wrap_socket(sock, server_side=True)
    except FileNotFoundError:
        logging.warning("SSL certificates not found. Running without encryption.")
        return sock

def validate_input(user_input):
    if not re.match("^[a-zA-Z0-9_]+$", user_input):
        raise ValueError("Invalid characters detected. Only alphanumeric and underscore are allowed.")

def print_banner():
    """Print colorful ASCII art banner."""
    banner = [
        colored(r" ___ _                      _    _          ", "cyan"),
        colored(r"/ __| |_ _ _ ___ __ _ _ __ | |  (_)_ _  ___ ", "green"),
        colored(r"\__ \  _| '_/ -_) _` | '  \| |__| | ' \\/ -_)", "yellow"),
        colored(r"|___/\__|_| \___\__,_|_|_|_|____|_|_||_\___|", "red"),
        colored("\n         -Made by L1avZh\n", "magenta")
    ]
    print("\n".join(banner))

class ChatServer:
    def __init__(self, host='0.0.0.0', port=None):
        self.host = host
        self.port = port if port else find_free_port()
        self.clients = {}
        self.executor = ThreadPoolExecutor(max_workers=10)

    def broadcast(self, message, exclude_client=None):
        """Send a message to all connected clients except the sender."""
        for client, nickname in self.clients.items():
            if client != exclude_client:
                try:
                    client.send(message)
                except Exception as e:
                    logging.error(f"Error sending message to {nickname}: {e}")
                    self.remove_client(client)

    def remove_client(self, client):
        """Remove a disconnected client from the server."""
        if client in self.clients:
            nickname = self.clients.pop(client)
            client.close()
            leave_msg = colored(f'{nickname} left the chat!', 'red')
            self.broadcast(leave_msg.encode('ascii'))
            logging.info(f"{nickname} has disconnected.")

    def handle_client(self, client):
        """Handle messages from a single client."""
        nickname = self.clients[client]
        while True:
            try:
                message = client.recv(1024)
                if not message:
                    break
                colored_message = colored(f"{nickname}: {message.decode('ascii')}", 'green')
                self.broadcast(colored_message.encode('ascii'), client)
            except Exception as e:
                logging.error(f"Error handling client {nickname}: {e}")
                break
        self.remove_client(client)

    def receive(self):
        """Accept new client connections."""
        server = secure_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((self.host, self.port))
            server.listen()
            logging.info(f"Server listening on {self.host}:{self.port}")
        except Exception as e:
            logging.error(f"Error starting server: {e}")
            sys.exit(1)

        try:
            while True:
                client, address = server.accept()
                logging.info(f"Connected with {str(address)}")
                client.send('NICK'.encode('ascii'))
                nickname = client.recv(1024).decode('ascii').strip()
                if nickname in self.clients.values():
                    client.send(colored("Nickname already in use. Disconnecting.", "red").encode('ascii'))
                    client.close()
                    continue
                validate_input(nickname)
                self.clients[client] = nickname
                logging.info(f"Nickname of the client is {nickname}")
                join_msg = colored(f'{nickname} joined the chat!', 'green')
                self.broadcast(join_msg.encode('ascii'))
                client.send(colored(f'Connected to the server on port {self.port}!', 'cyan').encode('ascii'))
                self.executor.submit(self.handle_client, client)
        except KeyboardInterrupt:
            logging.info("Server shutting down...")
            for client in list(self.clients.keys()):
                self.remove_client(client)
            sys.exit(0)

def run_server():
    print_banner()
    config = load_config()
    server = ChatServer(host=config['host'], port=config['port'])
    server.receive()

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    print_banner()
    run_server()

if __name__ == "__main__":
    main()
