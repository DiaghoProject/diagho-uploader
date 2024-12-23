#!/usr/bin/python3

import json
import hashlib
import inspect
import os
import shutil

# mail ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import socket
import yaml
import re
#---

import logging
from datetime import datetime


def setup_logger(filename):
    # Générer un nom de fichier de log avec un horodatage
    logs_directory = "logs"
    if not os.path.exists(logs_directory):
        os.makedirs(logs_directory)
    log_filename = os.path.join(logs_directory, filename)

    # Configuration du logger
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s][%(levelname)s][%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_filename),  # Nouveau fichier de log
            logging.StreamHandler()
        ]
    )


config_file = "config/config.yaml"

def load_config(config_file):
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print("Error loading config:", str(e))

def alert(content: str):
    try:
        config = load_config(config_file)
        recipients = config['emails']['recipients']
        send_mail_alert(recipients, content)
    except Exception as e:
        print("Error sending alert:", str(e))
    

def copy_and_remove_file(file_path, target_directory):
    if not os.path.exists(target_directory):
        os.makedirs(target_directory)
    shutil.copy(file_path, target_directory)
    print(f"File copied to: {target_directory}")
    os.remove(file_path)
    print(f"File removed from: {file_path}")

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
    Sends an email.
    
    Args:
        recipients (str): One or more recipients, separated by commas.
        subject (str): Subject of the email.
        content (str): Content of the email.
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
    Computes the MD5 hash of a file.

    Args:
        filepath (str): Absolute path to the file.

    Returns:
        str: The MD5 hash of the file as a hexadecimal string, or None in case of an error.
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

# Compare MD5  
def check_md5sum(checksum1, checksum2):
    """
    Compares two MD5 checksums.

    Args:
        checksum1 (str): The first MD5 checksum.
        checksum2 (str): The second MD5 checksum.

    Returns:
        bool: True if the MD5 checksums are identical, False otherwise.

    Raises:
        ValueError: If either of the MD5 checksums does not have the expected length of 32 characters.
    """
    print("\nCompare MD5sum :")
    print("checksum1:", checksum1)
    print("checksum2:", checksum2)
    # Validation des entrées
    if not isinstance(checksum1, str) or not isinstance(checksum2, str):
        raise TypeError("Les sommes de contrôle MD5 doivent être des chaînes de caractères.")
    # Vérifier que les deux sommes MD5 ont la même longueur (32 caractères pour MD5)
    if len(checksum1) != 32 or len(checksum2) != 32:
        raise ValueError("Les sommes de contrôle MD5 doivent avoir 32 caractères.")
    # Comparer les deux sommes MD5
    return checksum1.lower() == checksum2.lower()


# Check JSON format
def check_json_format(file_path):
    """
    Checks if the given file is properly formatted in JSON.

    Args:
        file_path (str): Path to the JSON file to check.

    Returns:
        bool: True if the file is properly formatted in JSON, False otherwise.
    """
        
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json.load(file)
        return True
    except json.JSONDecodeError as e:
        logging.getLogger("CHECK_JSON_FORMAT").error(f"File: '{file_path}' is not well-formatted: {e}")
        return False
    except FileNotFoundError:
        logging.getLogger("CHECK_JSON_FORMAT").error(f"File: '{file_path}' was not found.")
        return False
    except Exception as e:
        logging.getLogger("CHECK_JSON_FORMAT").error(f"An unexpected error occurred while checking the file '{file_path}': {e}")
        return False
    

def check_api_response(response, config, json_input, recipients):
    if response.status_code == 201:
        recipients = config['emails']['recipients']
        content = f"JSON file: {json_input}\n\nThe JSON configuration file was posted in Diagho successfully"
        send_mail_info(recipients, content)
        
    if response.status_code == 400:
        json_response = response.json()
        print("JSON Response:", json_response)
        json_string = json.dumps(response)
        
        # Vérif si patient déjà dans une famille
        search_string = "A person with the same identifier already exist, but is present in another family."
        if search_string in json_string:
            print("A person with the same identifier already exist, but is present in another family.")
            persons_content = response['json_response']['errors']['families'][4]['persons']
            recipients = config['emails']['recipients']
            content = f"JSON file: {json_input}\n\nA person with the same identifier already exist, but is present in another family :\n{persons_content}"
            send_mail_alert(recipients, content)