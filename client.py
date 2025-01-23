import socket
import threading
import sys
import logging
import json
from utils import colored, print_banner, load_config


def display_ui_banner():
    print(colored("\n============================", 'magenta'))
    print(colored("       StreamLine Chat      ", 'cyan'))
    print(colored("============================\n", 'magenta'))


class ChatClient:
    def __init__(self, host='127.0.0.1', port=None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.running = True

    def receive(self):
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    print(colored(f"{message}", 'cyan'))
            except ConnectionResetError:
                print(colored("\nServer closed the connection.", 'red'))
                self.running = False
                break
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                break

    def write(self):
        while self.running:
            try:
                message = input(colored("\n\u2192", "yellow")).strip()
                if message.lower() == '/exit':
                    print(colored("\nDisconnecting...", 'red'))
                    self.running = False
                    self.client.close()
                    break
                if message:
                    self.client.send((message + '\n').encode('utf-8'))
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                break

    def start(self, nickname):
        self.nickname = nickname
        try:
            self.client.connect((self.host, self.port))
            print(colored("\nConnected to the server! You can start chatting.", 'green'))
            self.client.send(self.nickname.encode('utf-8'))
            threading.Thread(target=self.receive, daemon=True).start()
            self.write()
        except ConnectionRefusedError:
            print(colored("\nUnable to connect to the server.", 'red'))
            sys.exit(1)


def run_client():
    display_ui_banner()
    config = load_config()

    host = input(colored("Enter server IP (press Enter for localhost): ", 'yellow')).strip()
    if not host:
        host = '127.0.0.1'

    port = input(colored("Enter server port (press Enter for default): ", 'yellow')).strip()
    try:
        port = int(port) if port else config.get('port', 12345)
    except ValueError:
        print(colored("Invalid port number. Please enter a valid integer.", 'red'))
        sys.exit(1)

    nickname = input(colored("Choose your nickname: ", 'yellow')).strip()
    if not nickname:
        print(colored("Nickname cannot be empty.", 'red'))
        sys.exit(1)

    client = ChatClient(host=host, port=port)
    client.start(nickname)


if __name__ == "__main__":
    print(colored("\nWelcome to StreamLine! Running server and client together.", 'cyan'))
    run_client()
