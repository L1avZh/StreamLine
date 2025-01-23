import socket
import sys
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from utils import colored, print_banner, find_free_port, load_config

class ChatServer:
    def __init__(self, host='0.0.0.0', port=None):
        self.host = host
        self.port = port if port else find_free_port()
        self.clients = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.server_running = True

    def broadcast(self, message, exclude_client=None):
        for client, nickname in list(self.clients.items()):
            if client != exclude_client:
                try:
                    client.send(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error sending message to {nickname}: {e}")
                    self.remove_client(client)

    def remove_client(self, client):
        if client in self.clients:
            nickname = self.clients.pop(client)
            client.close()
            self.broadcast(colored(f'{nickname} left StreamLine!', 'red'))
            logging.info(f"{nickname} disconnected.")

    def handle_client(self, client):
        nickname = self.clients[client]
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                if not message:
                    break
                self.broadcast(colored(f"{nickname}: {message}", 'green'), client)
            except Exception as e:
                logging.error(f"Error handling client {nickname}: {e}")
                break
        self.remove_client(client)

    def receive(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((self.host, self.port))
            server.listen()
            print(colored(f"🚀 StreamLine running on {self.host}:{self.port}", 'cyan'))

            while self.server_running:
                client, address = server.accept()
                logging.info(f"Connected with {str(address)}")
                nickname = client.recv(1024).decode('utf-8').strip()

                if nickname in self.clients.values():
                    client.send(colored("Nickname already in use.", "red").encode('utf-8'))
                    client.close()
                    continue

                self.clients[client] = nickname
                logging.info(f"New client joined: {nickname}")
                print(colored(f'{nickname} joined StreamLine!', 'green'))
                self.executor.submit(self.handle_client, client)
        except KeyboardInterrupt:
            logging.info("Server shutting down...")
            sys.exit(0)

def run_server():
    print_banner()
    config = load_config()
    server = ChatServer(host=config['host'], port=config['port'])
    server.receive()
