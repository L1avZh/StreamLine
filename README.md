# StreamLine Chat Application

StreamLine is a terminal-based chat application that allows users to communicate over a network. You can run it in server mode to host a chat, and multiple clients can connect to it from local or public networks.


## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/L1avZh/StreamLine.git
   cd StreamLine
   ```

## Usage


![](https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYXFpc20ydDE2Y3Vxc3d4d25kYWU4ZHRpeDFhNXIyeHkyMHRnNGdqaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/GTRAA5xJOlUrsMd0QL/giphy.gif)


### 1. Running the Server

1. **Start the application**:
   ```bash
   python main.py
   ```
2. **At the prompt**, type `1` (then press Enter) to run in server mode.
   ```
   StreamLine running on 0.0.0.0:5000
   ```

### 2. Running a Client

```bash
   python main.py
   ```
 2. **At the prompt**, type `2` (then press Enter) to run in client mode.
 
 
   * only clients can talk to each other
  

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


## Contributing

Contributions, suggestions, and bug reports are welcomed!  
- Fork the repository, create a feature branch, and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

---

