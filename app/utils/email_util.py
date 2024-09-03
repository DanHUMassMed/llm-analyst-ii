import smtplib
from socket import gaierror
from email.mime.text import MIMEText
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
import logging
import os
from dotenv import load_dotenv 
load_dotenv()

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

SMTP_SERVER  = os.getenv('SMTP_SERVER')
SMTP_LOGIN   = os.getenv('SMTP_LOGIN')
SMTP_PASSWD  = os.getenv('SMTP_PASSWD')
REDIRECT_URL = os.getenv('REDIRECT_URL')


def email_results(receiver, the_file, message_text=None):
    index_of_sep = the_file.rfind(os.path.sep)
    filename = the_file[index_of_sep + 1:-4]

    subject = 'AI Researchers Results'
    sender = "dphiggins@gmail.com"
    if not message_text:
        message_text = """
        Please find attached your research results.

        We would appreciate any feedback on your experience.

        Thank you for being a beta tester!
        """
    message = construct_message_with_attachment(subject, sender, receiver, message_text, the_file)
    send_message_ssl(sender, receiver, message)

def email_verification(receiver, verification_token, first_name):

    subject = 'Verify your email'
    sender = "llm_researcher@gmail.com"
    
    message_html = f"""
    <html>
  <body>
    <h1>Verify Your Email</h1>
    <p>Dear { first_name },</p>
    <p>Thank you for registering with us. To activate your account, please click the verification button below.</p>
    <div>
        <a href="{REDIRECT_URL}/verify/{verification_token}" target="_blank">
        <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
            Verify Email
        </button>
        </a>
    </div>
    <p>Best regards,</p>
    <p>Dan</p>
  </body>
</html>
    """
    message = construct_message_with_html(subject, sender, receiver, message_html=message_html)
    send_message_ssl(sender, receiver, message)

def construct_message_with_html(subject, sender, receiver, message_text=None, message_html=None):
    the_message = MIMEMultipart()
    the_message['Subject'] = subject
    the_message['To'] = receiver
    the_message['From'] = sender
    the_message.preamble = 'I am not using a MIME-aware mail reader.\n'

    if message_text:
        the_message.attach(MIMEText(message_text, "plain"))
    if message_html:
        the_message.attach(MIMEText(message_html, "html"))

    return the_message.as_string()


def construct_message_with_attachment(subject, sender, receiver, message_text, the_file):
    zip_file = open(the_file, 'rb')
    the_message = MIMEMultipart()
    the_message['Subject'] = subject
    the_message['To'] = receiver
    the_message['From'] = sender
    the_message.preamble = 'I am not using a MIME-aware mail reader.\n'

    the_message.attach(MIMEText(message_text, "plain"))

    msg = MIMEBase('application', 'zip')
    msg.set_payload(zip_file.read())
    encoders.encode_base64(msg)

    index_of_sep = the_file.rfind(os.path.sep)
    msg.add_header('Content-Disposition', 'attachment', filename=the_file[index_of_sep+1:])
    the_message.attach(msg)
    return the_message.as_string()


def send_message(sender, receiver, message):
    try:
        port = 587
        with smtplib.SMTP(SMTP_SERVER, port) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_LOGIN, SMTP_PASSWD)
            server.sendmail(sender, receiver, message)
    except (gaierror, ConnectionRefusedError):
        logging.debug("Failed to connect to the server. Bad connection settings?")
    except smtplib.SMTPServerDisconnected:
        logging.debug("Failed to connect to the server. Wrong user/password?")
    except smtplib.SMTPException as e:
        logging.debug("SMTP error occurred: {}".format(str(e)))
    else:
        logging.debug("SMTP sent to: {}".format(receiver))


def send_message_ssl(sender, receiver, message):
    try:
        port = 465
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, port, context=context) as server:
            server.login(SMTP_LOGIN, SMTP_PASSWD)
            server.sendmail(sender, receiver, message)
    except (gaierror, ConnectionRefusedError):
        logging.debug("Failed to connect to the server. Bad connection settings?")
    except smtplib.SMTPServerDisconnected:
        logging.debug("Failed to connect to the server. Wrong user/password?")
    except smtplib.SMTPException as e:
        logging.debug("SMTP error occurred: {}".format(str(e)))
    else:
        logging.debug("SMTP sent to: {}".format(receiver))


if __name__ == "__main__":
    receiver="dphiggins@gmail.com"
    verification_token="19953b29c9094280a1d46b39cc3d86a6"
    first_name="Dan"
    email_verification(receiver, verification_token, first_name)