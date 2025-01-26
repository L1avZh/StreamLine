# main.py

import argparse
import logging
import sys
import os
import time

from Utils.utils import print_banner, colored, load_config, clear_screen, loading_animation
from Server.server import run_server
from Client.client import run_client

def parse_args():
    """
    Parse optional CLI arguments for running StreamLine.
    """
    parser = argparse.ArgumentParser(description="StreamLine Chat Application")
    parser.add_argument(
        '--mode',
        choices=['server', 'client'],
        help="Run in server mode or client mode. If not provided, you'll be prompted."
    )
    return parser.parse_args()

def main():
    """
    Entry point of the StreamLine application.
    Allows optional CLI arguments or user prompts for server/client mode.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    config_file = 'config.json'
    config = load_config(config_file)
    
    args = parse_args()
    
    if not args.mode:
        print_banner()
        print(colored("Welcome to StreamLine!", 'cyan'))
        print(colored("1. Run as Server", 'yellow'))
        print(colored("2. Run as Client", 'yellow'))
        choice = input(colored("Enter your choice (1/2): ", 'yellow')).strip()
        if choice == '1':
            args.mode = 'server'
        elif choice == '2':
            args.mode = 'client'
        else:
            print(colored("Invalid choice. Exiting.", 'red'))
            sys.exit(1)

    try:
        clear_screen()
        loading_animation("Starting StreamLine...")
        if args.mode == 'server':
            logging.info("Starting server mode...")
            run_server()
        elif args.mode == 'client':
            logging.info("Starting client mode...")
            run_client()
        else:
            logging.error("Invalid mode argument.")
            sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down.")
        sys.exit(0)
    except Exception as e:
        logging.exception(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
