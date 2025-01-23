import socket
import threading
import sys
import logging
import os
import time
from Utils.utils import colored, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


def display_ui_banner():
    """
    Print a simple banner for the chat UI.
    """
    print(colored("\n============================", 'magenta'))
    print(colored("       StreamLine Chat      ", 'cyan'))
    print(colored("============================\n", 'magenta'))


def clear_screen():
    """
    Clears the terminal screen for both Windows and Unix-based systems.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def loading_animation(text="Connecting to chat"):
    """
    Displays a loading animation, rotating progress bars a few times.
    """
    animation = ["[■□□□□]", "[■■□□□]", "[■■■□□]", "[■■■■□]", "[■■■■■]"]
    for _ in range(3):  # repeat animation 3 times
        for frame in animation:
            sys.stdout.write(f"\r{colored(text, 'cyan')} {colored(frame, 'green')}")
            sys.stdout.flush()
            time.sleep(0.2)
    sys.stdout.write("\n")


class ChatClient:
    """
    A simple TCP chat client that uses threading to handle
    simultaneous send/receive with a chat server.
    """

    def __init__(self, host='127.0.0.1', port=12345, nickname="User"):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

    def receive(self):
        """
        Continuously receives messages from the server.
        If server sends 'NICK', send the nickname.
        Otherwise, print messages to the console.
        """
        while self.running:
            try:
                message = self.client.recv(1024).decode('utf-8')
                if not message:
                    # Empty message means server closed the connection
                    raise ConnectionResetError("Server disconnected.")

                if message == 'NICK':
                    self.client.send(self.nickname.encode('utf-8'))
                else:
                    print(colored(f"{message}", 'cyan'))
            except (ConnectionResetError, ConnectionAbortedError):
                print(colored("\nServer closed the connection.", 'red'))
                break
            except Exception as e:
                logging.error(f"Error receiving message: {e}")
                break

        # If we exit the loop, shut down
        self.close_connection()

    def write(self):
        """
        Continuously reads user input and sends it to the server.
        Exits if the user types '/exit'.
        """
        while self.running:
            try:
                message = input(colored("\n→ ", "yellow")).strip()

                if message.lower() == '/exit':
                    print(colored("\nDisconnecting...", 'red'))
                    break

                if message:
                    self.client.send((message + '\n').encode('utf-8'))
            except EOFError:
                # Handle Ctrl+D or similar
                break
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                break

        self.close_connection()

    def close_connection(self):
        """
        Gracefully shut down the socket and stop the client.
        """
        if self.running:
            self.running = False
            try:
                self.client.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # Socket might already be closed
            self.client.close()
            print(colored("Connection closed.", 'red'))

    def start(self):
        """
        Connects to the server and starts the receive/write threads.
        """
        try:
            self.client.connect((self.host, self.port))
        except ConnectionRefusedError:
            print(colored("Unable to connect to the server.", 'red'))
            sys.exit(1)
        except Exception as e:
            logging.error(f"Unexpected error connecting to server: {e}")
            sys.exit(1)

        clear_screen()
        loading_animation()
        print(colored("\nWelcome to StreamLine Chat!", 'green'))
        print(colored("You have successfully connected!\n", 'magenta'))
        print(colored("Type your messages below. Type '/exit' to leave.\n", 'yellow'))
        print(colored("=" * 40, 'cyan'))

        # Send nickname
        self.client.send(self.nickname.encode('utf-8'))

        # Start the threads
        receive_thread = threading.Thread(target=self.receive, daemon=True)
        receive_thread.start()
        self.write()


def run_client():
    """
    Main logic for running the chat client.
    Gathers user inputs for IP, port, and nickname, then starts the client.
    """
    display_ui_banner()
    config = load_config()

    default_host = '127.0.0.1'
    default_port = config.get('port', 12345)

    # Gather host input
    host_input = input(colored("Enter server IP (press Enter for localhost): ", 'yellow')).strip()
    host = host_input or default_host

    # Gather port input
    port_input = input(colored(f"Enter server port (press Enter for {default_port}): ", 'yellow')).strip()
    if port_input:
        if not port_input.isdigit():
            print(colored("Invalid port number. Please enter a valid integer.", 'red'))
            sys.exit(1)
        else:
            port = int(port_input)
    else:
        port = default_port

    # Gather nickname
    nickname = input(colored("Choose your nickname: ", 'yellow')).strip()
    if not nickname.isalnum():
        print(colored("Nickname should contain only letters and numbers.", 'red'))
        sys.exit(1)

    client = ChatClient(host=host, port=port, nickname=nickname)
    client.start()


if __name__ == "__main__":
    print(colored("\nWelcome to StreamLine! Running client...", 'cyan'))
    run_client()
