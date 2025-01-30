# Import necessary modules
import json
import socket
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict

# Optional: configure your logging format here (or in your main script)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

# Define ANSI color codes for styling text output in the terminal
class Colors:
    """
    ANSI color code definitions for styling text output in the terminal.
    """
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

# Mapping of color names to ANSI codes
COLOR_MAP = {
    'red': Colors.RED,
    'green': Colors.GREEN,
    'yellow': Colors.YELLOW,
    'blue': Colors.BLUE,
    'magenta': Colors.MAGENTA,
    'cyan': Colors.CYAN,
    'white': Colors.WHITE
}

# Function to wrap text in ANSI color codes
def colored(text: str, color: str) -> str:
    """
    Wrap the given text in ANSI color codes.

    :param text: The text to be colored.
    :param color: The color name (must match a key in COLOR_MAP).
    :return: The colored text string, or the original text if the color is invalid.
    """
    return f"{COLOR_MAP.get(color, Colors.RESET)}{text}{Colors.RESET}"

# Function to print the application's banner in colored ASCII art
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

# Function to find and return a free ephemeral port
def find_free_port() -> int:
    """
    Finds and returns a free ephemeral port by binding a socket to ('', 0).

    :return: An unused port number assigned by the OS.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

# Function to load configuration from a JSON file
def load_config(config_file):
    """
    Load configuration from a JSON file.
    """
    try:
        with open(config_file, 'r') as file:
            config = json.load(file)
            logging.info(f"Config loaded: {config}")
            return config
    except FileNotFoundError:
        logging.error(f"Config file '{config_file}' not found.")
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from config file '{config_file}'.")
    except Exception as e:
        logging.error(f"Unexpected error reading config file '{config_file}': {e}")
    return {}

# Function to get a value from the config, returning a default if the key is not found or the value is None
def get_config_value(config, key, default=None):
    """
    Get a value from the config, returning a default if the key is not found or the value is None.
    """
    value = config.get(key, default)
    if value is None:
        logging.warning(f"Config key '{key}' is missing or None. Using default: {default}")
        return default
    return value

# Function to clear the terminal screen on Windows or Unix-based systems
def clear_screen():
    """
    Clears the terminal screen on Windows or Unix-based systems.
    """
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

# Function to display a short "spinner" animation in the terminal
def loading_animation(text="Loading..."):
    """
    Displays a short "spinner" animation in the terminal.
    """
    animation = ["|", "/", "-", "\\"]
    for i in range(20):  # adjust for how long you want the animation to run
        frame = animation[i % len(animation)]
        sys.stdout.write(f"\r{frame} {text}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r")  # move to the beginning of the line after animation finishes
    sys.stdout.flush()

