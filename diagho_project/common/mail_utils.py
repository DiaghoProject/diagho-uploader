import inspect
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import socket
import yaml
import re

from common.log_utils import *

def send_mail(recipients: str, subject: str, content: str, config='config/config.yaml'):
    """
    Sends an email.
    
    Args:
        recipients (str): One or more recipients, separated by commas.
        subject (str): Subject of the email.
        content (str): Content of the email.
    """
    function_name = inspect.currentframe().f_code.co_name
    
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
        log_message("EMAIL", "ERROR", f"Invalid email address in recipient list: {recipient_list}")
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
        log_message(function_name, "INFO", f"Email sent successfully to: {recipient_list}")
    except Exception as e:
        log_message(function_name, "ERROR", f": {str(e)}")
        

# Ces deux fonctions pour spécifier l'objet du mail
def send_mail_alert(recipients: str, content: str):
    if recipients:
        function_name = inspect.currentframe().f_code.co_name
        log_message(function_name, "WARNING", f"Send alert.")
        subject = "[ALERT] Diagho-Uploader"
        send_mail(recipients, subject, content)

    
def send_mail_info(recipients: str, content: str):
    if recipients:
        function_name = inspect.currentframe().f_code.co_name
        log_message(function_name, "INFO", f"Send info.")
        subject = "[INFO] Diagho-Uploader"
        send_mail(recipients, subject, content)
