import json
import socket
import logging
from pathlib import Path
from typing import Dict

# Optional: configure your logging format here (or in your main script)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


class Colors:
    """
    ANSI color code definitions for styling text output in the terminal.
    If you need cross-platform compatibility (particularly older Windows CMD),
    consider using `import colorama` and `colorama.init()`.
    """
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


COLOR_MAP = {
    'red': Colors.RED,
    'green': Colors.GREEN,
    'yellow': Colors.YELLOW,
    'blue': Colors.BLUE,
    'magenta': Colors.MAGENTA,
    'cyan': Colors.CYAN,
    'white': Colors.WHITE
}


def colored(text: str, color: str) -> str:
    """
    Wrap the given text in ANSI color codes.

    :param text: The text to be colored.
    :param color: The color name (must match a key in COLOR_MAP).
    :return: The colored text string, or the original text if the color is invalid.
    """
    return f"{COLOR_MAP.get(color, Colors.RESET)}{text}{Colors.RESET}"


def print_banner() -> None:
    """
    Prints the application's banner in colored ASCII art.
    """
    banner_lines = [
        r" ___ _                      _    _          ",
        r"/ __| |_ _ _ ___ __ _ _ __ | |  (_)_ _  ___ ",
        r"\__ \  _| '_/ -_) _` | '  \| |__| | ' \/ -_)",
        r"|___/\__|_| \___\__,_|_|_|_|____|_|_||_\___|",
        "         - Made by L1avZh\n"
    ]

    # Cycle through colors for each line in the banner
    colors = ["cyan", "green", "yellow", "red", "magenta"]
    for i, line in enumerate(banner_lines):
        print(colored(line, colors[i % len(colors)]))


def find_free_port() -> int:
    """
    Finds and returns a free ephemeral port by binding a socket to ('', 0).

    :return: An unused port number assigned by the OS.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def load_config(filename: str = "config.json") -> Dict[str, str]:
    """
    Loads and parses a JSON config file. If the file is not found or invalid,
    logs an error and returns default config values.

    :param filename: The path to the JSON config file (default 'config.json').
    :return: A dictionary of configuration options. Keys: 'host' (str), 'port' (int).
    """
    config_path = Path(filename)
    default_config = {'host': '127.0.0.1', 'port': find_free_port()}

    if not config_path.exists():
        logging.error(f"Config file '{filename}' not found. Using defaults.")
        return default_config

    try:
        with config_path.open('r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Ensure 'host' and 'port' exist in final config
        final_config = {
            'host': config_data.get('host', default_config['host']),
            'port': int(config_data.get('port', find_free_port()))
        }
        return final_config
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file '{filename}': {e}. Using defaults.")
        return default_config
    except ValueError as e:
        logging.error(f"Error parsing config file '{filename}': {e}. Using defaults.")
        return default_config
    except Exception as e:
        logging.error(f"Unexpected error reading config file '{filename}': {e}")
        return default_config

