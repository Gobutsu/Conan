from config import init_account
from utils import run_web_server, get_email_senders, fetch_mailbox
import argparse
import json

def main():    
    parser = argparse.ArgumentParser(description="Conan by Gobutsu")
    parser.add_argument("-r", "--restore", help="Launches the web server with a provided JSON file", metavar="FILE")
    parser.add_argument("-e", "--email", help="Email address to use")
    parser.add_argument("-m", "--mbox", help="Import a mbox file", metavar="FILE")
    args = parser.parse_args()

    if args.email:
        EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER = init_account(args.email)
        
        senders = get_email_senders(EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER)
        run_web_server(senders, EMAIL_ADDRESS)
    elif args.restore:
        file = open(args.restore, "r")
        file_json = json.load(file)
        domains = file_json['domains']
        email = file_json['email']
        run_web_server(domains, email)
    elif args.mbox:
        senders = fetch_mailbox(args.mbox)
        run_web_server(senders, args.mbox)
    else:
        parser.print_usage()


if __name__ == "__main__":
    main()