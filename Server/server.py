import os
import sys
import logging
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from Utils.utils import colored, print_banner, find_free_port, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


def clear_screen():
    """
    Clears the terminal screen on Windows or Unix-based systems.
    """
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


def loading_animation(text="Loading the server..."):
    """
    Displays a short "spinner" animation in the terminal.
    """
    animation = ["|", "/", "-", "\\"]
    for i in range(20):  # adjust for how long you want the animation to run
        # Use modulo to cycle through animation frames
        frame = animation[i % len(animation)]
        sys.stdout.write(f"\r{frame} {text}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\n")  # move to next line after animation finishes


class ChatServer:
    """
    A simple threaded chat server using sockets and a ThreadPoolExecutor.
    """

    def __init__(self, host='0.0.0.0', port=None):
        self.host = host
        self.port = port if port else find_free_port()
        self.clients = {}  # Map: socket -> nickname
        self.lock = threading.Lock()
        self.server_running = True

        self.executor = ThreadPoolExecutor(max_workers=10)

    def broadcast(self, message, exclude_client=None):
        """
        Send a message to all connected clients except 'exclude_client'.
        """
        with self.lock:
            for client, nickname in list(self.clients.items()):
                if client == exclude_client:
                    continue
                try:
                    client.send(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error sending message to {nickname}: {e}")
                    self.remove_client(client)

    def remove_client(self, client):
        """
        Remove a client socket from the server, broadcast the departure, and log info.
        """
        with self.lock:
            nickname = self.clients.get(client, "Unknown")
            if client in self.clients:
                del self.clients[client]

        try:
            client.close()
        except Exception as e:
            logging.error(f"Error closing client socket for {nickname}: {e}")

        self.broadcast(colored(f"{nickname} left StreamLine!", 'red'))
        logging.info(f"{nickname} disconnected.")

    def handle_client(self, client):
        """
        Handle incoming messages from a single client socket.
        """
        with self.lock:
            nickname = self.clients.get(client, "Unknown")

        while self.server_running:
            try:
                message = client.recv(1024)
                if not message:
                    # Client disconnected
                    break

                decoded_msg = message.decode('utf-8').strip()
                # If you want to parse commands, do it here:
                # if decoded_msg.startswith('/'):
                #     self.handle_command(decoded_msg, client)
                # else:
                self.broadcast(colored(f"{nickname}: {decoded_msg}", 'green'), exclude_client=client)

            except (ConnectionResetError, ConnectionAbortedError):
                break
            except Exception as e:
                logging.error(f"Error handling client {nickname}: {e}")
                break

        self.remove_client(client)

    def receive(self):
        """
        Accept new client connections, request a nickname, handle duplicates, and start threads.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            logging.info(f"Server listening on {self.host}:{self.port}")
            print(colored(f"🚀 StreamLine running on {self.host}:{self.port}", 'cyan'))

            while self.server_running:
                try:
                    client, address = server_socket.accept()
                except OSError:
                    # If the socket is closed while shutting down
                    break

                logging.info(f"Connected with {str(address)}")

                # First message from the client should be the nickname
                nickname_data = client.recv(1024)
                if not nickname_data:
                    client.close()
                    continue

                nickname = nickname_data.decode('utf-8').strip()

                # Check if nickname already in use
                with self.lock:
                    if nickname in self.clients.values():
                        client.send(colored("Nickname already in use. Disconnecting.", "red").encode('utf-8'))
                        client.close()
                        logging.warning(f"Duplicate nickname attempt: {nickname}")
                        continue

                    self.clients[client] = nickname

                logging.info(f"New client joined: {nickname}")
                print(colored(f"{nickname} joined StreamLine!", 'green'))

                # Submit the handler to the pool
                self.executor.submit(self.handle_client, client)

        except KeyboardInterrupt:
            logging.info("Server shutting down via KeyboardInterrupt...")
        except Exception as e:
            logging.error(f"Unexpected server error: {e}")
        finally:
            self.shutdown(server_socket)

    def shutdown(self, server_socket):
        """
        Cleanly shut down the server, closing all sockets.
        """
        self.server_running = False

        # Close the listening socket
        try:
            server_socket.close()
        except Exception as e:
            logging.error(f"Error closing server socket: {e}")

        # Close all client connections
        with self.lock:
            for client in list(self.clients.keys()):
                self.remove_client(client)

        # Shutdown the thread pool
        self.executor.shutdown(wait=True)
        logging.info("Server has shut down.")


def run_server():
    """
    Entry point to run the chat server with configuration from file.
    """
    print_banner()
    config = load_config()

    host = config.get('host', '0.0.0.0')
    port = config.get('port') or find_free_port()

    server = ChatServer(host=host, port=port)
    server.receive()


def main():
    """
    Main function to let the user choose if they want to run the server.
    Shows a small loading animation if they choose 'server',
    then starts the server.
    """
    choice = input("Type 'server' to run the server, or anything else to exit: ").strip().lower()
    if choice == 'server':
        clear_screen()
        loading_animation("Starting the server...")
        print("Server is starting up... Press Ctrl+C to stop.\n")
        run_server()
    else:
        print("Exiting...")
        sys.exit(0)


if __name__ == "__main__":
    main()
