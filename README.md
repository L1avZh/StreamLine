# StreamLine Chat Application

StreamLine is a terminal-based chat application that allows users to communicate over a network. The application can be run in both server and client modes, enabling public and local network chatting.

## Features

- **Two-way communication**: Server can participate in the chat alongside clients.
- **Public Accessibility**: Run the server publicly with port forwarding or Ngrok.
- **Colored Terminal Output**: Improved user experience with ANSI color codes.
- **Automatic Port Selection**: If no port is provided, the server will choose an available one.
- **Multi-threading**: Handles multiple clients efficiently.

## Prerequisites

Ensure you have the following installed on your system:

- Python 3.7+

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/L1avZh/StreamLine.git
   cd StreamLine
   ```

## Usage

### Running the Server

1. Open a terminal and start the server:
   ```bash
   python main.py
   ```
2. Choose `1` to start as the server.
3. The server will display the assigned IP and port to connect clients.

### Running the Client

1. Open another terminal and start the client:
   ```bash
   python main.py
   ```
2. Choose `2` to run in client mode.
3. Enter the server's public or local IP and port to join the chat.

### Public Access Setup

#### 1. Port Forwarding

If you want to run the chat publicly, forward the selected port (e.g., `5000`) on your router to allow external connections.

#### 2. Using Ngrok

Alternatively, you can expose the server to the public internet using Ngrok:

```bash
ngrok tcp 5000
```

Ngrok will provide a public address like `tcp://0.tcp.ngrok.io:12345` which clients can use to connect.

## Configuration

The application configuration is stored in `config.json`:

```json
{
    "host": "0.0.0.0",
    "port": null
}
```

- `host`: Set to `0.0.0.0` to allow external connections.
- `port`: Leave as `null` to assign a random free port or specify a custom one.

## Example

1. Run the server:
   ```bash
   python main.py
   ```
   Output:
   ```
   🚀 Server running on 0.0.0.0:5000
   ```
2. Run a client and connect to the server:
   ```bash
   python main.py
   ```
   Input server IP and port, then start chatting.

## Troubleshooting

- **Can't connect to the server?**
  - Ensure the server's firewall allows the specified port.
  - If using Ngrok, make sure it is running.
  
- **Invalid Port Error?**
  - Make sure you're entering a valid port number (1-65535).

## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

## License

This project is licensed under the MIT License.

