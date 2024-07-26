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
logging.basicConfig(
    level=logging.INFO,                     # Définir le niveau de log minimum
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Format du message
    handlers=[
        logging.FileHandler('app.log'),     # Enregistrer les logs dans un fichier
        logging.StreamHandler()             # Afficher les logs sur la console
    ]
)

config_file = "config/config.yaml"

def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def alert(content: str):
    config = load_config(config_file)
    recipients = config['emails']['recipients']
    send_mail_alert(recipients, content)
    

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

# Compare MD5  
def check_md5sum(checksum1, checksum2):
    """
    Compare deux sommes de contrôle MD5.

    Args:
        checksum1 (str): La première somme de contrôle MD5.
        checksum2 (str): La deuxième somme de contrôle MD5.

    Returns:
        bool: True si les sommes de contrôle MD5 sont identiques, sinon False.

    Raises:
        ValueError: Si l'une des sommes de contrôle MD5 n'a pas la longueur attendue de 32 caractères.
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
    Vérifie si le fichier donné est bien formaté en JSON.

    Args:
        file_path (str): Chemin vers le fichier JSON à vérifier.

    Returns:
        bool: True si le fichier est bien formaté en JSON, False sinon.
    """
        
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json.load(file)
        logging.info(f"File: '{file_path}' is well-formatted.")
        return True
    except json.JSONDecodeError as e:
        logging.error(f"File: '{file_path}' is not well-formatted: {e}")
        return False
    except FileNotFoundError:
        logging.error(f"File: '{file_path}' was not found.")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred while checking the file '{file_path}': {e}")
        return False