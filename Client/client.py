# Import necessary modules
import socket
import threading
import sys
import logging
import os
import time
from Utils.utils import colored, load_config, get_config_value, clear_screen, loading_animation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# Define the ChatClient class
class ChatClient:
    def __init__(self, host, port, nickname, password=None):
        # Initialize the client with host, port, nickname, and optional password
        self.host = host
        self.port = port
        self.nickname = nickname
        self.password = password
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

    def start(self):
        # Start the client and connect to the server
        try:
            self.client.connect((self.host, self.port))
            if self.password:
                self.client.send(self.password.encode('utf-8'))
                response = self.client.recv(1024).decode('utf-8')
                if "Invalid password" in response:
                    print(colored(response, 'red'))
                    self.client.close()
                    sys.exit(1)
                elif "Password accepted" in response:
                    print(colored(response, 'green'))
            threading.Thread(target=self.receive_messages).start()
            self.send_messages()
        except ConnectionRefusedError:
            print(colored("Unable to connect to the server.", 'red'))
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error connecting to server: {e}")
            sys.exit(1)

    def receive_messages(self):
        # Receive messages from the server
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if message:
                    print(colored(message, 'green'))
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                self.close_connection()
                break

    def send_messages(self):
        # Send messages to the server
        while self.running:
            try:
                message = input()
                if message.lower() == '/exit':
                    print(colored("\nDisconnecting...", 'red'))
                    break

                if message:
                    full_message = f"{self.nickname}: {message}"
                    self.client.send(full_message.encode('utf-8'))
            except EOFError:
                break
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                break

        self.close_connection()

    def close_connection(self):
        # Close the connection to the server
        if self.running:
            self.running = False
            try:
                self.client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.client.close()
            print(colored("Connection closed.", 'red'))

# Function to run the client
def run_client():
    config_file = 'config.json'
    config = load_config(config_file)
    
    default_host = get_config_value(config, 'host', 'localhost')
    default_port = get_config_value(config, 'server_port', 12345)
    
    host = input(colored(f"Enter server host (default: {default_host}): ", 'yellow')).strip() or default_host
    port_input = input(colored(f"Enter server port (default: {default_port}): ", 'yellow')).strip()
    port = int(port_input) if port_input else default_port

    password = input(colored("Enter server password (if any): ", 'yellow')).strip()

    nickname = input(colored("Choose your nickname: ", 'yellow')).strip()
    if not nickname.isalnum():
        print(colored("Nickname should contain only letters and numbers.", 'red'))
        sys.exit(1)

    client = ChatClient(host=host, port=port, nickname=nickname, password=password)
    client.start()

# Main entry point of the script
if __name__ == "__main__":
    clear_screen()
    loading_animation("Starting client...")
    print(colored("\nWelcome to StreamLine! Running client...", 'cyan'))
    run_client()
