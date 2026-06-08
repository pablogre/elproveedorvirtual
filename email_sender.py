# ============================================================
# email_sender.py
# Módulo reutilizable para enviar emails vía SMTP
# ============================================================
# Uso:
#   from email_sender import enviar_email
#
#   ok, msg = enviar_email(
#       destinatario='proveedor@mail.com',
#       asunto='Orden de Compra OC 0001-00000001',
#       cuerpo_html='<p>Te adjuntamos la OC...</p>',
#       adjunto_bytes=pdf_bytes,
#       nombre_adjunto='OC_0001-00000001.pdf',
#       mime_adjunto='application/pdf'
#   )
#   if not ok:
#       # mostrar error → msg
#
# Credenciales en config_cliente.py:
#   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS,
#   SMTP_FROM, SMTP_FROM_NAME
# ============================================================

import smtplib
import ssl
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr, formatdate, make_msgid

import config_cliente as CFG


def _cfg(nombre, default=''):
    return getattr(CFG, nombre, default) or default


def enviar_email(destinatario, asunto, cuerpo_html,
                 adjunto_bytes=None, nombre_adjunto=None,
                 mime_adjunto='application/pdf',
                 cc=None, bcc=None,
                 cuerpo_texto=None):
    """
    Envía un email vía SMTP (Gmail u otro).

    Returns:
        (bool, str): (True, 'OK') si se envió, (False, 'motivo') si falló.
    """
    host      = _cfg('SMTP_HOST', 'smtp.gmail.com')
    port      = int(_cfg('SMTP_PORT', 587))
    user      = _cfg('SMTP_USER', '')
    password  = _cfg('SMTP_PASS', '')
    from_addr = _cfg('SMTP_FROM', user)
    from_name = _cfg('SMTP_FROM_NAME', '')

    if not user or not password:
        return False, 'SMTP no configurado (falta SMTP_USER o SMTP_PASS en config_cliente.py)'

    if not destinatario or '@' not in destinatario:
        return False, f'Destinatario invalido: {destinatario}'

    try:
        msg = MIMEMultipart('mixed')
        msg['From']       = formataddr((from_name, from_addr)) if from_name else from_addr
        msg['To']         = destinatario
        msg['Subject']    = asunto
        msg['Date']       = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid()

        if cc:
            msg['Cc'] = ', '.join(cc)

        # Cuerpo texto + html
        alternative = MIMEMultipart('alternative')
        if cuerpo_texto:
            alternative.attach(MIMEText(cuerpo_texto, 'plain', 'utf-8'))
        else:
            fallback = cuerpo_html.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
            fallback = re.sub(r'<[^>]+>', '', fallback)
            alternative.attach(MIMEText(fallback, 'plain', 'utf-8'))
        alternative.attach(MIMEText(cuerpo_html, 'html', 'utf-8'))
        msg.attach(alternative)

        # Adjunto
        if adjunto_bytes and nombre_adjunto:
            maintype, subtype = (mime_adjunto.split('/', 1) + ['octet-stream'])[:2]
            if maintype == 'application':
                part = MIMEApplication(adjunto_bytes, _subtype=subtype)
            else:
                part = MIMEApplication(adjunto_bytes)
            part.add_header('Content-Disposition', 'attachment', filename=nombre_adjunto)
            msg.attach(part)

        # RCPT TO
        to_all = [destinatario]
        if cc:  to_all.extend(cc)
        if bcc: to_all.extend(bcc)

        context = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, context=context, timeout=20) as server:
                server.login(user, password)
                server.sendmail(from_addr, to_all, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                if port == 587:
                    server.starttls(context=context)
                    server.ehlo()
                server.login(user, password)
                server.sendmail(from_addr, to_all, msg.as_string())

        return True, 'OK'

    except smtplib.SMTPAuthenticationError as e:
        return False, ('Autenticacion SMTP fallida. Verifica SMTP_USER/SMTP_PASS '
                       '(usa una "app password" de Gmail, no la contrasena normal). '
                       f'Detalle: {e}')
    except smtplib.SMTPRecipientsRefused as e:
        return False, f'Destinatario rechazado: {e}'
    except smtplib.SMTPException as e:
        return False, f'Error SMTP: {e}'
    except Exception as e:
        return False, f'Error inesperado al enviar mail: {e}'