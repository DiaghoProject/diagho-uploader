#!/usr/bin/python3

import json

# mail ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import yaml
#---



# Pretty print json string
def pretty_print_json_string(string):
    """
    Pretty print a string formatting in JSON

    Arguments:
    string : input string
    """
    json_string = json.dumps(string)
    json_dict = json.loads(json_string)
    print(json.dumps(json_dict, indent = 1)) 


# Send mail
def send_mail(recipients: str, subject: str, content: str):
    """
    Envoi de mail.

    Arguments:
        recipients : un ou plusieurs destinataires, séparés par des virgules
        subject : objet du mail
        content : contenu du mail
    """
    
    # Lire la configuration dans fichier YAML
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)
        
    server = smtplib.SMTP()
    # Paramètres du serveur SMTP
    smtp_server = config['smtp']['server']
    smtp_port = config['smtp']['port']
    use_tls = config['smtp']['use_tls']
    
    server.connect(smtp_server)
    server.helo()

    # Adresse e-mail de l'expéditeur
    from_email = config['smtp']['from_email_format'].format(hostname=socket.gethostname())

    # Création du message
    body = content
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = recipients
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Connexion au serveur SMTP
    try:
        # Envoi de l'e-mail
        server.sendmail(from_email, recipients.split(','), message.as_string())
        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", str(e))
        
def send_mail_alert(recipients: str, content: str):
    subject = "[ALERT] TEST Diagho-Uploader"
    send_mail(recipients, subject, content)
    
def send_mail_info(recipients: str, content: str):
    subject = "[INFO] TEST Diagho-Uploader"
    send_mail(recipients, subject, content)