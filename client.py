import socket
import threading
import sys
from utils import colored, print_banner


class ChatClient:
    def __init__(self, host='127.0.0.1', port=None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port

    def receive(self):
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('ascii'))
                else:
                    print(colored(message, 'cyan'))
            except:
                print(colored("Disconnected from server!", 'red'))
                self.client.close()
                break

    def write(self):
        while True:
            message = input(colored("→ ", "yellow"))
            self.client.send(message.encode('ascii'))

    def start(self, nickname):
        self.nickname = nickname
        try:
            self.client.connect((self.host, self.port))
            threading.Thread(target=self.receive, daemon=True).start()
            self.write()
        except ConnectionRefusedError:
            print(colored("Unable to connect to the server.", 'red'))
            sys.exit(1)


def run_client():
    print_banner()
    port = input(colored("Enter server port: ", 'yellow')).strip()
    try:
        port = int(port)
    except ValueError:
        print(colored("Invalid port number. Please enter a valid integer.", 'red'))
        sys.exit(1)

    nickname = input(colored("Choose your nickname: ", 'yellow')).strip()
    if not nickname:
        print(colored("Nickname cannot be empty.", 'red'))
        sys.exit(1)

    client = ChatClient(port=port)
    client.start(nickname)
