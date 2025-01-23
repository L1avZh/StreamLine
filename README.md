Below is an updated version of your README that reflects recent changes—particularly the prompt to type `"server"` at startup and the loading animation before the server starts. If you’ve made additional changes to the client code (for example, integrating it into the same script or providing a separate `client.py`), feel free to adjust the instructions accordingly.

---

# StreamLine Chat Application

StreamLine is a terminal-based chat application that allows users to communicate over a network. You can run it in server mode to host a chat, and multiple clients can connect to it from local or public networks.

## Features

- **Two-way Communication**: The server can participate in the chat alongside clients.  
- **Public Accessibility**: Easily host publicly using port forwarding or Ngrok.  
- **Colored Terminal Output**: Enjoy visually distinct messages with ANSI color codes.  
- **Automatic Port Selection**: If no port is provided, the server finds an available one.  
- **Multi-threading**: Efficiently handles multiple clients at once.  
- **Loading Animation**: Enjoy a brief spinner animation while the server starts up.

## Prerequisites

- **Python 3.7+** (tested on macOS, Windows, and Linux)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/L1avZh/StreamLine.git
   cd StreamLine
   ```

## Usage

### 1. Running the Server

1. **Start the application**:
   ```bash
   python main.py
   ```
2. **At the prompt**, type `1` (then press Enter) to run in server mode.
3. A small **loading spinner** will appear, then you’ll see server logs. It will display the assigned IP and port, for example:
   ```
   StreamLine running on 0.0.0.0:5000
   ```

### 2. Running a Client

```bash
   python main.py
   ```
 2. **At the prompt**, type `2` (then press Enter) to run in client mode.
 
 
   * only client can talk to each other
  

## Public Access Setup

To allow external connections over the internet, you have common approaches:

**Port Forwarding**:  
   - Log into your router and forward the server’s chosen port (e.g., `5000`) to your local machine.
   - Share your **public IP and port** with others so they can connect.

## Configuration

Configuration is stored in `config.json`. An example:

```json
{
    "host": "0.0.0.0",
    "port": null
}
```
- **host**: Defaults to `0.0.0.0` for external connections; you can set it to `127.0.0.1` for local-only.
- **port**: If set to `null`, a random free port is assigned. Otherwise, set a custom port number.

## Example

1. **Run the server**:
   ```bash
   python main.py
   ```
   When prompted, choose `server`. You’ll see something like:
   ```
   | Starting the server...
   ...
   StreamLine running on 0.0.0.0:5000
   ```
2. **Run a client**:
   - In another terminal or machine, choose client.
   - Input the server’s IP (or public Ngrok address) and port to join the chat.
   - Start chatting!
   * only client can talk to each other

## Troubleshooting

- **Cannot connect to the server**:  
  - Check your firewall settings or router’s port forwarding.  
  - If using Ngrok, ensure it’s running and that you’re using the correct Ngrok address.
- **Invalid port error**:  
  - Ensure you’ve entered a valid port number (1–65535).  
  - If you still have issues, leave `port` in `config.json` as `null` so it auto-selects a free one.

## Contributing

Contributions, suggestions, and bug reports are welcomed!  
- Fork the repository, create a feature branch, and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

---

**Enjoy secure and colorful chatting with StreamLine!**