import imaplib
import email
from email.header import decode_header
import time
import os
import threading
from config import PENDING_DIR, IMAP_SERVER, IMAP_PORT, IMAP_USER, IMAP_PASS

def decode_mime_words(s):
    try:
        if not s:
            return ""
        return "".join(
            word.decode(encoding or 'utf8') if isinstance(word, bytes) else word
            for word, encoding in decode_header(s)
        )
    except Exception:
        return str(s)

def fetch_email_attachments():
    """Conecta ao IMAP, procura emails não lidos, guarda os anexos em PENDING_DIR e marca como lidos."""
    if not IMAP_SERVER or not IMAP_USER or not IMAP_PASS:
        return
        
    try:
        # Conectar ao servidor IMAP
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select("inbox")

        # Pesquisar e-mails não lidos
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return
            
        email_ids = messages[0].split()
        for email_id in email_ids:
            status, data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                continue
                
            msg = email.message_from_bytes(data[0][1])
            subject = decode_mime_words(msg.get("Subject", ""))
            
            # Percorrer as partes do e-mail
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename = part.get_filename()
                if filename:
                    filename = decode_mime_words(filename)
                    # Verifica extensão
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.pdf', '.jpg', '.jpeg', '.png']:
                        # Criar nome seguro para n haver sobreposições
                        secure_filename = f"email_{int(time.time())}_{filename}"
                        filepath = os.path.join(PENDING_DIR, secure_filename)
                        
                        # Guardar anexo em PENDING_DIR (o Dashboard apanha-o aqui)
                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))
                            
        mail.logout()
    except Exception as e:
        print(f"Erro no serviço de Email Fetcher: {e}")

def start_email_polling(interval_minutes=15):
    """Bloqueia a thread correndo o fetch a cada intervalo."""
    while True:
        fetch_email_attachments()
        time.sleep(interval_minutes * 60)

def start_email_service_thread():
    """Lança a daemon."""
    if IMAP_SERVER and IMAP_USER and IMAP_PASS:
        t = threading.Thread(target=start_email_polling, kwargs={'interval_minutes': 5}, daemon=True)
        t.start()
