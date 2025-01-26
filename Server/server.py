import json
import socket
import threading
import logging
import os
from Utils.utils import colored, print_banner, find_free_port, load_config, get_config_value, clear_screen, loading_animation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

clients = []

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
            except Exception as e:
                logging.error(f"Error broadcasting message: {e}")
                client.close()
                clients.remove(client)

def handle_client(client_socket, server_password):
    if server_password:
        client_socket.send("Enter password: ".encode('utf-8'))
        password = client_socket.recv(1024).decode('utf-8').strip()
        if password != server_password:
            client_socket.send("Invalid password. Disconnecting.".encode('utf-8'))
            client_socket.close()
            return
        else:
            client_socket.send("Password accepted. Welcome!".encode('utf-8'))
    
    clients.append(client_socket)
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            logging.info(f"Received message: {message}")
            broadcast(message, client_socket)
        except Exception as e:
            logging.error(f"Error handling client: {e}")
            break
    client_socket.close()
    clients.remove(client_socket)

def run_server():
    config_file = 'config.json'
    config = load_config(config_file)
    
    server_port = find_free_port()
    config['server_port'] = server_port
    
    server_password = input(colored("Set server password (leave blank for no password): ", 'yellow')).strip()
    config['server_password'] = server_password if server_password else None
    
    with open(config_file, 'w') as file:
        json.dump(config, file)
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', server_port))
    server_socket.listen(5)
    logging.info(f"Server started on port {server_port}")

    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Accepted connection from {addr}")
        threading.Thread(target=handle_client, args=(client_socket, server_password)).start()

if __name__ == "__main__":
    clear_screen()
    loading_animation("Starting server...")
    run_server()
