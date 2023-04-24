import requests
from jinja2 import Environment, FileSystemLoader
from http.server import SimpleHTTPRequestHandler
from config import PROVIDERS_URL, JDM_URL, WEB_PORT
import json
import os
import imaplib
from tqdm import tqdm
import email
import http.server
import datetime
import mailbox
from collections import defaultdict
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
import tldextract
from datetime import timezone

class CustomRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, domains=None, email_address=None, **kwargs):
        self.domains = domains
        self.email_address = email_address
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path == "/":
            self._serve_template()
        elif self.path == "/csv":
            self._serve_csv()
        elif self.path == "/json":
            self._serve_json()
        else:
            self._serve_file_or_404()

    def _serve_json(self):
        dump = {}
        dump['email'] = self.email_address
        dump['domains'] = [dict(x) for x in self.domains]
        dump['timestamp'] = str(datetime.datetime.now())

        dump = json.dumps(dump).encode()
        
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Disposition", "attachment; filename=\"domains.json\"")
        self.end_headers()
        self.wfile.write(dump)

    def _serve_template(self):
        env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'web')))
        template = env.get_template('index.html')
        content = template.render(domains=self.domains, email=self.email_address).encode()
        
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content)

    def _serve_file_or_404(self):
        file_path = os.path.join(os.path.dirname(__file__), 'web', self.path[1:])
        
        if os.path.isfile(file_path):
            self.send_response(200)
            content_type = self.guess_type(file_path)
            self.send_header("Content-type", content_type)
            self.end_headers()
            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())
        else:
            self.send_error(404, "File not found")

def get_top_level_domain(domain):
    extracted = tldextract.extract(domain)
    return f"{extracted.domain}.{extracted.suffix}"
    
def get_email_providers():
    response = requests.get(PROVIDERS_URL)
    response.raise_for_status()
    return set(response.text.splitlines())

def get_jdm_sites():
    response = requests.get(JDM_URL)
    response.raise_for_status()
    return response.json()

def add_message(senders, providers, mail):
    sender = mail['from']
    sender_str = str(sender.encode('utf-8'))
    sender_name, sender_email = email.utils.parseaddr(sender_str)
    sender_email = get_top_level_domain(sender_email.split("@")[-1]).lower().replace('\'', '')
    if not sender_email in providers:
        senders[sender_email].append(mail)

def fetch_mailbox(mbox_file):
    providers = get_email_providers()

    senders = defaultdict(list)
    print("Reading mbox file...")
    mbox = mailbox.mbox(mbox_file)
    for message in tqdm(mbox, desc="Fetching emails"):
        add_message(senders, providers, message)

    return process_senders(senders)

def get_email_senders(email_address, email_password, IMAP_SERVER):
    providers = get_email_providers()

    senders = defaultdict(list)

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(email_address, email_password)

    mail.select("inbox")

    _, message_numbers_raw = mail.search(None, "ALL")
    message_numbers = message_numbers_raw[0].split()

    for message_number in tqdm(message_numbers, desc="Fetching emails"):
        _, msg_data = mail.fetch(message_number, "(BODY[HEADER.FIELDS (FROM DATE SUBJECT)])")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                add_message(senders, providers, message)

    mail.logout()
    return process_senders(senders)

def get_header(header_text):
    if not header_text:
        return '(no subject)'
    return str(make_header(decode_header(header_text)))


def process_senders(senders):
    sites = get_jdm_sites()
    site_domain_mapping = {
        get_top_level_domain(jdm_domain): site
        for site in sites
        for jdm_domain in site['domains']
    }

    def create_domain_object(sender_email, messages):
        site = site_domain_mapping.get(sender_email, {})

        last_emails = []
        messages = sorted(messages, key=lambda msg: parsedate_to_datetime(msg['date']).replace(tzinfo=timezone.utc))
        for msg in messages[-5:]:
            decoded_subject = get_header(msg['subject'])
            last_emails.append({'subject': decoded_subject, 'date': msg['date']})

        return {
            'domain': sender_email,
            'difficulty': site.get('difficulty', 'unknown'),
            'notes': site.get('notes'),
            'url': site.get('url'),
            'email': site.get('email'),
            'last_emails': json.dumps(last_emails)
        }

    domains = [create_domain_object(sender_email, messages) for sender_email, messages in tqdm(senders.items(), desc="Processing mails...")]

    return domains

def run_web_server(domains, email_address):
    print("Running web server...")
    
    server_address = ("", WEB_PORT)
    handler = lambda *args, **kwargs: CustomRequestHandler(*args, domains=domains, email_address=email_address, **kwargs)
    httpd = http.server.HTTPServer(server_address, handler)

    print("Server is running at http://localhost:{}".format(WEB_PORT))

    httpd.serve_forever()