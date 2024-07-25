#!/usr/bin/python3

import json
import hashlib
import inspect

# mail ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import socket
import yaml
import re
#---


config_file = "config/config.yaml"

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def alert(content: str):
    config = load_config(config_file)
    recipients = config['emails']['recipients']
    send_mail_alert(recipients, content)
    

# Pretty print json string
def pretty_print_json_string(string):
    """
    Pretty print a JSON string.

    Arguments:
        json_str : str : The JSON string to be pretty printed.
    """
    try:
        json_string = json.dumps(string)
        json_dict = json.loads(json_string)
        print(json.dumps(json_dict, indent = 1))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON string: {e}")
     


# Send mail
def send_mail(recipients: str, subject: str, content: str, config='config/config.yaml'):
    """
    Send email.

    Arguments:
        recipients : un ou plusieurs destinataires, séparés par des virgules
        subject : objet du mail
        content : contenu du mail
    """
    
    # Lire la configuration dans fichier YAML
    with open(config, 'r') as file:
        config = yaml.safe_load(file)
        
    # Paramètres du serveur SMTP
    smtp_server = config['smtp']['server']
    smtp_port = config['smtp']['port']
    use_tls = config['smtp']['use_tls']
    from_email = config['smtp']['from_email_format'].format(hostname=socket.gethostname())
    
    # Validation des adresses email
    def validate_email(email):
        regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(regex, email) is not None
    recipient_list = [email.strip() for email in recipients.split(',')]
    if not all(validate_email(email) for email in recipient_list):
        print("Invalid email address in recipient list.")
        return
    
    # Création du message
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = ', '.join(recipient_list)
    message['Subject'] = subject
    message.attach(MIMEText(content, 'plain'))
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.helo()
            if use_tls:
                server.starttls()
            server.sendmail(from_email, recipient_list, message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", str(e))
        
def send_mail_alert(recipients: str, content: str):
    subject = "[ALERT] TEST Diagho-Uploader"
    send_mail(recipients, subject, content)
    
def send_mail_info(recipients: str, content: str):
    subject = "[INFO] TEST Diagho-Uploader"
    send_mail(recipients, subject, content)

# Calcul MD5
def md5(filepath):
    """
    Calcule le hash MD5 d'un fichier.

    Arguments:
        filepath (str): Chemin absolu du fichier.

    Returns:
        str: Le hash MD5 du fichier sous forme de chaîne hexadécimale, ou None en cas d'erreur. 
    """
    function_name = inspect.currentframe().f_code.co_name
    
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (IOError, FileNotFoundError) as e:
        content = f"FUNCTION: {function_name}:\n\nErreur lors de l'ouverture ou de la lecture du fichier : {e}"
        alert(content)
        print(f"Erreur lors de l'ouverture ou de la lecture du fichier : {e}")
        return None