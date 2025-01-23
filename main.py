# main.py

import argparse
import logging
import sys

from Utils.utils import print_banner, colored
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

    args = parse_args()

    # Print the banner in white/blue
    print_banner()

    try:
        if args.mode is None:
            # No CLI mode specified, prompt the user in bright colors
            print(colored("Choose mode:", "white"))
            print(colored("1. Server", "blue"))
            print(colored("2. Client", "blue"))

            choice = input(colored("Enter your choice (1/2): ", "yellow")).strip()
            if choice == '1':
                logging.info("Starting server mode...")
                run_server()
            elif choice == '2':
                logging.info("Starting client mode...")
                run_client()
            else:
                logging.error("Invalid choice provided.")
                print(colored("Invalid choice. Exiting.", 'red'))
                sys.exit(1)

        else:
            # A --mode argument was supplied
            if args.mode == 'server':
                logging.info("Starting server mode (CLI-based)...")
                run_server()
            elif args.mode == 'client':
                logging.info("Starting client mode (CLI-based)...")
                run_client()
            else:
                # Should never happen, but just in case
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
