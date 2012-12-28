from django.core.mail import *
from django.core.mail.message import *
from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from django.conf import settings

"""
Utilities for sending email with attachments
"""

class SafeMIMEMultipart(MIMEMultipart): 
    def __setitem__(self, name, val): 
        "Forbids multi-line headers, to prevent header injection." 
        if '\n' in val or '\r' in val: 
            raise BadHeaderError, "Header values can't contain newlines (got %r for header %r)" % (val, name) 
        if name == "Subject": 
            val = Header(val, settings.DEFAULT_CHARSET) 
        MIMEMultipart.__setitem__(self, name, val) 
 
    def attachFile(self, filename, content, mimetype, content_id = None): 
        maintype, subtype = mimetype.split('/', 1) 
        msg = MIMEBase(maintype, subtype) 
        if content == None:
            fp = open(filename, 'rb')
            content = fp.read()
            fp.close()
        msg.set_payload(content) 
        Encoders.encode_base64(msg) 
        msg.add_header('Content-Disposition', 'attachment', filename=filename.replace('/', '_')) 
        if content_id != None:
            msg.add_header('Content-ID', content_id)
        MIMEMultipart.attach(self, msg) 

class HTMLEmail(EmailMessage):
    def __init__(self, *args, **kwargs):
        self.html_message = kwargs.pop('html_message', None)
        super(HTMLEmail, self).__init__(*args, **kwargs)

    def message(self):
        msg = SafeMIMEMultipart('related')
        alt_msg = SafeMIMEMultipart('alternative') 
        alt_msg.attach(MIMEText(self.body.encode(settings.DEFAULT_CHARSET), 'plain', settings.DEFAULT_CHARSET)) 
        alt_msg.attach(MIMEText(self.html_message.encode(settings.DEFAULT_CHARSET), 'html', settings.DEFAULT_CHARSET))
        msg.attach(alt_msg)
        
        msg['Subject'] = self.subject
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to)
        msg['Date'] = formatdate()
        msg['Message-ID'] = make_msgid()
        if self.bcc:
            msg['Bcc'] = ', '.join(self.bcc)
        return msg

def send_html_mail_with_attachments(subject, message, html_message, from_email, recipient_list, fail_silently=False, auth_user=None, auth_password=None): 
    connection = SMTPConnection(username=auth_user, password=auth_password, fail_silently=fail_silently)
    return HTMLEmail(unicode(subject), message, from_email, recipient_list, connection=connection, html_message=html_message).send()