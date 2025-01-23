import socket
import sys
from utils import colored, print_banner


def run_client():
    print_banner()
    host = input(colored("Enter server IP (local/public): ", 'yellow')).strip()
    port = input(colored("Enter server port: ", 'yellow')).strip()

    try:
        port = int(port)
    except ValueError:
        print(colored("Invalid port number.", 'red'))
        sys.exit(1)

    nickname = input(colored("Choose your nickname: ", 'yellow')).strip()
    if not nickname:
        print(colored("Nickname cannot be empty.", 'red'))
        sys.exit(1)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print(colored(f"Connected to {host}:{port}", 'green'))
        client_socket.send(nickname.encode('ascii'))

        while True:
            message = input(colored("→ ", "yellow"))
            client_socket.send(message.encode('ascii'))
    except ConnectionRefusedError:
        print(colored("Unable to connect. Check the IP/port and try again.", 'red'))
