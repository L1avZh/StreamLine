import logging
import sys

from utils import print_banner, colored
from server import run_server
from client import run_client

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    print_banner()
    print(colored("Choose mode:", 'cyan'))
    print(colored("1. Server", 'green'))
    print(colored("2. Client", 'green'))

    choice = input(colored("Enter your choice (1/2): ", 'yellow')).strip()
    if choice == '1':
        run_server()
    elif choice == '2':
        run_client()
    else:
        print(colored("Invalid choice. Exiting.", 'red'))
        sys.exit(1)

if __name__ == "__main__":
    main()
