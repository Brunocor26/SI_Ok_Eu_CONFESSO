import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MAILPIT_HOST = 'localhost'
MAILPIT_PORT = 1025

def enviar_email_cifrado(destinatario, assunto, codigo_acesso, corpo_cifrado):
    texto = (
        f"Para ler este e-mail, aceda a https://OK-Eu-CONFESSO.xxx\n"
        f"e confirme a receção com o código: {codigo_acesso}\n\n"
        f"--- CORPO CIFRADO ---\n{corpo_cifrado}\n--------------------"
    )

    html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background: #1a1a2e; padding: 24px 32px; }}
    .header h1 {{ color: #e2b96f; margin: 0; font-size: 20px; letter-spacing: 1px; }}
    .body {{ padding: 32px; color: #333; }}
    .body p {{ line-height: 1.6; }}
    .cta {{ display: inline-block; margin: 20px 0; padding: 12px 24px; background: #e2b96f; color: #1a1a2e; font-weight: bold; text-decoration: none; border-radius: 4px; }}
    .code-block {{ background: #f0f0f0; border-left: 4px solid #e2b96f; padding: 16px; font-family: monospace; font-size: 13px; word-break: break-all; margin: 16px 0; }}
    .footer {{ background: #f0f0f0; padding: 16px 32px; font-size: 12px; color: #888; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>OK — Eu Confesso</h1></div>
    <div class="body">
      <p>Recebeu uma mensagem cifrada através do sistema <strong>OK-Eu-CONFESSO</strong>.</p>
      <p>Para ler o conteúdo, aceda ao sistema e confirme a receção com o seu código de acesso:</p>
      <a class="cta" href="http://localhost:5173/decrypt">Aceder ao Sistema</a>
      <p><strong>Código de Acesso:</strong></p>
      <div class="code-block">{codigo_acesso}</div>
      <p><strong>Corpo da mensagem cifrado:</strong></p>
      <div class="code-block">{corpo_cifrado}</div>
      <p style="color:#888; font-size:13px;">Se não solicitou esta mensagem, ignore este email.</p>
    </div>
    <div class="footer">Sistema OK-Eu-CONFESSO &mdash; Mensagem gerada automaticamente</div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart('alternative')
    msg['From'] = 'sistema@ok-eu-confesso.xxx'
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(texto, 'plain', 'utf-8'))
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(MAILPIT_HOST, MAILPIT_PORT) as smtp:
            smtp.sendmail(msg['From'], [destinatario], msg.as_string())
    except Exception as e:
        print(f"Erro a enviar email (Mailpit inativo?): {e}")


def enviar_notificacao_leitura(email_emissor: str, receipt_text: str):
    texto = f"A sua mensagem foi lida.\n\nDetalhes do recibo:\n{receipt_text}"

    html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
    .header {{ background: #1a1a2e; padding: 24px 32px; }}
    .header h1 {{ color: #e2b96f; margin: 0; font-size: 20px; letter-spacing: 1px; }}
    .body {{ padding: 32px; color: #333; }}
    .body p {{ line-height: 1.6; }}
    .code-block {{ background: #f0f0f0; border-left: 4px solid #e2b96f; padding: 16px; font-family: monospace; font-size: 13px; word-break: break-all; margin: 16px 0; }}
    .footer {{ background: #f0f0f0; padding: 16px 32px; font-size: 12px; color: #888; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>OK — Eu Confesso</h1></div>
    <div class="body">
      <p>A sua mensagem foi <strong>lida</strong> pelo destinatário.</p>
      <p><strong>Detalhes do recibo:</strong></p>
      <div class="code-block">{receipt_text}</div>
      <p style="color:#888; font-size:13px;">Mensagem gerada automaticamente pelo sistema OK-Eu-CONFESSO.</p>
    </div>
    <div class="footer">Sistema OK-Eu-CONFESSO &mdash; Mensagem gerada automaticamente</div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart('alternative')
    msg['From'] = 'sistema@ok-eu-confesso.xxx'
    msg['To'] = email_emissor
    msg['Subject'] = 'A sua mensagem foi lida'
    msg.attach(MIMEText(texto, 'plain', 'utf-8'))
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP(MAILPIT_HOST, MAILPIT_PORT) as smtp:
            smtp.sendmail(msg['From'], [email_emissor], msg.as_string())
    except Exception as e:
        print(f"Erro a enviar notificação de leitura: {e}")
