import socket
import threading
import sys
import logging
import os
import time
from utils import colored, print_banner, load_config

def display_ui_banner():
    print(colored("\n============================", 'magenta'))
    print(colored("       StreamLine Chat      ", 'cyan'))
    print(colored("============================\n", 'magenta'))

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def loading_animation(text="Connecting to chat"):
    animation = ["[■□□□□]", "[■■□□□]", "[■■■□□]", "[■■■■□]", "[■■■■■]"]
    for _ in range(3):
        for frame in animation:
            sys.stdout.write(f"\r{colored(text, 'cyan')} {colored(frame, 'green')}")
            sys.stdout.flush()
            time.sleep(0.2)
    sys.stdout.write("\n")

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
            except (ConnectionResetError, ConnectionAbortedError):
                print(colored("\nServer closed the connection.", 'red'))
                self.running = False
                self.client.close()
                break
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                break


    def write(self):
        while self.running:
            try:
                message = input(colored("\n→", "yellow")).strip()
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
            clear_screen()
            loading_animation()
            print(colored("\nWelcome to StreamLine Chat!", 'green'))
            print(colored("You have successfully connected!\n", 'magenta'))
            print(colored("Type your messages below. Type '/exit' to leave.\n", 'yellow'))
            print(colored("="*40, 'cyan'))
            self.client.send(self.nickname.encode('utf-8'))
            threading.Thread(target=self.receive, daemon=True).start()
            self.write()
        except ConnectionRefusedError:
            print(colored("\nUnable to connect to the server.", 'red'))
            sys.exit(1)

def run_client():
    display_ui_banner()
    config = load_config()

    host = input(colored("Enter server IP (press Enter for localhost): ", 'yellow')).strip() or '127.0.0.1'
    port_input = input(colored("Enter server port (press Enter for default): ", 'yellow')).strip()
    try:
        port = int(port_input) if port_input else config.get('port', 12345)
    except ValueError:
        if not port_input.isdigit():
            print(colored("Invalid port number. Please enter a valid integer.", 'red'))
            sys.exit(1)

    nickname = input(colored("Choose your nickname: ", 'yellow')).strip()
    if not nickname.isalnum():
        print(colored("Nickname should contain only letters and numbers.", 'red'))
        sys.exit(1)

    client = ChatClient(host=host, port=port)
    client.start(nickname)

if __name__ == "__main__":
    print(colored("\nWelcome to StreamLine! Running server and client together.", 'cyan'))
    run_client()
