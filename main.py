import socket
import threading
import sys
import random


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


def print_banner():
    """Print colorful ASCII art banner."""
    banner = [
        colored(r" ___ _                      _    _          ", "cyan"),
        colored(r"/ __| |_ _ _ ___ __ _ _ __ | |  (_)_ _  ___ ", "green"),
        colored(r"\__ \  _| '_/ -_) _` | '  \| |__| | ' \/ -_)", "yellow"),
        colored(r"|___/\__|_| \___\__,_|_|_|_|____|_|_||_\___|", "red"),
        colored("\n         -Made by L1avZh\n", "magenta")
    ]
    print("\n".join(banner))


class ChatServer:
    def __init__(self, host='127.0.0.1', port=None):
        self.host = host
        self.port = port if port else find_free_port()
        self.clients = []
        self.nicknames = []

    def broadcast(self, message, _client=None):
        """Send a message to all connected clients except the sender."""
        for client in self.clients:
            if client != _client:
                try:
                    client.send(message)
                except:
                    self.remove_client(client)

    def remove_client(self, client):
        """Remove a disconnected client from the server."""
        if client in self.clients:
            index = self.clients.index(client)
            self.clients.remove(client)
            client.close()
            nickname = self.nicknames[index]
            self.nicknames.remove(nickname)
            leave_msg = colored(f'{nickname} left the chat!', 'red')
            self.broadcast(leave_msg.encode('ascii'))

    def handle_client(self, client):
        """Handle messages from a single client."""
        while True:
            try:
                message = client.recv(1024)
                colored_message = colored(message.decode('ascii'), 'green')
                self.broadcast(colored_message.encode('ascii'), client)
            except:
                self.remove_client(client)
                break

    def receive(self):
        """Accept new client connections."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server.bind((self.host, self.port))
            server.listen()
            print(colored(f"Server is listening on {self.host}:{self.port}", 'blue'))
        except Exception as e:
            print(colored(f"Error starting server: {e}", 'red'))
            sys.exit(1)

        while True:
            try:
                client, address = server.accept()
                print(colored(f"Connected with {str(address)}", 'green'))

                client.send('NICK'.encode('ascii'))
                nickname = client.recv(1024).decode('ascii')
                self.nicknames.append(nickname)
                self.clients.append(client)

                print(colored(f"Nickname of the client is {nickname}", 'yellow'))
                join_msg = colored(f'{nickname} joined the chat!', 'green')
                self.broadcast(join_msg.encode('ascii'))
                client.send(colored(f'Connected to the server on port {self.port}!', 'cyan').encode('ascii'))

                thread = threading.Thread(target=self.handle_client, args=(client,))
                thread.start()
            except Exception as e:
                print(colored(f"Error accepting connection: {e}", 'red'))


class ChatClient:
    def __init__(self, host='127.0.0.1', port=None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port

    def receive(self):
        """Receive messages from the server."""
        while True:
            try:
                message = self.client.recv(1024).decode('ascii')
                if message == 'NICK':
                    self.client.send(self.nickname.encode('ascii'))
                else:
                    print(colored(message, 'cyan'))
            except:
                print(colored("An error occurred! Disconnecting.", 'red'))
                self.client.close()
                break

    def write(self):
        """Send messages to the server."""
        while True:
            message = f'{self.nickname}: {input(colored("→ ", "yellow"))}'
            self.client.send(message.encode('ascii'))

    def start(self, nickname, server_port):
        """Connect to the server and start communication."""
        try:
            self.nickname = nickname
            self.client.connect((self.host, server_port))

            receive_thread = threading.Thread(target=self.receive)
            receive_thread.start()

            write_thread = threading.Thread(target=self.write)
            write_thread.start()
        except Exception as e:
            print(colored(f"Connection error: {e}", 'red'))
            sys.exit(1)


def run_server():
    """Start the chat server."""
    print_banner()
    server = ChatServer()
    print(colored(f"Server started on port {server.port}", 'blue'))
    server.receive()


def run_client():
    """Start the chat client."""
    print_banner()
    port = int(input(colored("Enter server port: ", 'yellow')))
    client = ChatClient()
    nickname = input(colored("Choose your nickname: ", 'yellow'))
    client.start(nickname, port)


def main():
    """Main function to choose between server and client mode."""
    print_banner()
    print(colored("Choose mode:", 'cyan'))
    print(colored("1. Server", 'green'))
    print(colored("2. Client", 'green'))

    choice = input(colored("Enter your choice (1/2): ", 'yellow'))

    if choice == '1':
        run_server()
    elif choice == '2':
        run_client()
    else:
        print(colored("Invalid choice. Exiting.", 'red'))
        sys.exit(1)


if __name__ == "__main__":
    main()