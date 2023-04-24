import json
import os
from getpass import getpass

def init_account(email_address):
    imap_list = json.load(open(os.path.join(os.path.dirname(__file__), 'IMAP.json')))
    IMAP_SERVER = None
    for value in imap_list:
        if email_address.endswith(value['email_provider']):
            IMAP_SERVER = value['imap_server']
            print("Found IMAP server for your email address: " + IMAP_SERVER)
            break

    if IMAP_SERVER is None:
        IMAP_SERVER = input("Could not find IMAP server for your email address. Enter it manually: ")

    EMAIL_PASSWORD = getpass("Enter your email password: ")

    return email_address, EMAIL_PASSWORD, IMAP_SERVER

PROVIDERS_URL = 'https://raw.githubusercontent.com/derhuerst/emailproviders/master/generate/domains.txt'
JDM_URL = 'https://raw.githubusercontent.com/jdm-contrib/jdm/master/_data/sites.json'
WEB_PORT = 8000