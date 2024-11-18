from pyrogram import Client, filters
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
import threading

api_id = "29166633"
api_hash = "ed46990d7d7519c61aceb8f66a3452b9"
session_string = ""
app = Client("my_account", api_id=api_id, api_hash=api_hash, session_string=session_string)

sending = False
sent_count = 0
stop_event = threading.Event()
default_sleep_time = 10

def send_emails(sender_emails, email_password, recipient_emails, email_body, email_subject):
    global sending, sent_count, stop_event
    failed_senders = set()
    
    while not stop_event.is_set():
        for sender_email in sender_emails:
            if sender_email in failed_senders:
                continue
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, email_password)
                
                for recipient_email in recipient_emails:
                    msg = MIMEMultipart()
                    msg['From'] = sender_email
                    msg['To'] = recipient_email
                    msg['Subject'] = email_subject
                    msg.attach(MIMEText(email_body, 'plain'))
                    
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                    sent_count += 1
                    time.sleep(default_sleep_time)
                
                server.quit()
            except smtplib.SMTPAuthenticationError as e:
                failed_senders.add(sender_email)
                app.send_message("me", f"حدث خطأ في المصادقة أثناء إرسال البريد الإلكتروني عبر {sender_email}: {e}")
                break
            except smtplib.SMTPRecipientsRefused as e:
                app.send_message("me", f"فشل إرسال البريد الإلكتروني عبر {sender_email} إلى {recipient_email}: {e}")
            except Exception as e:
                app.send_message("me", f"حدث خطأ غير متوقع أثناء إرسال البريد الإلكتروني عبر {sender_email}: {e}")
                failed_senders.add(sender_email)
                break

@app.on_message(filters.chat("me"))
def handle_message(client, message):
    global sending, sent_count, stop_event

    if message.text.lower().strip() == "إيقاف":
        stop_event.set()
        sending = False
        client.send_message("me", f"تم إيقاف إرسال البريد الإلكتروني بعد إرسال {sent_count} رسالة.")
        return
    
    if message.text.lower().strip() == "فحص":
        client.send_message("me", f"عدد الرسائل المرسلة: {sent_count}")
        return

    lines = message.text.split("\n")
    if len(lines) < 4:
        client.send_message("me", "يرجى التأكد من إدخال المعلومات في الترتيب الصحيح:\n1- الايميل الذي سيرسل منه، الباسورد\n2- ايميل المستلم\n3- كليشة الارسال\n4- الموضوع")
        return

    lines = [line.split('-', 1)[-1].strip() for line in lines]
    sender_emails = [email.strip() for email in lines[0].strip().split(',')]
    recipient_emails = [email.strip() for email in lines[1].strip().split(',')]
    email_subject = lines[-1].strip()
    email_body = "\n".join(lines[2:-1]).strip()

    if len(sender_emails) == 0 or len(recipient_emails) == 0:
        client.send_message("me", "يرجى التأكد من إدخال عناوين البريد الإلكتروني بشكل صحيح")
        return

    email_password = lines[0].split(',')[1].strip()

    if not sending:
        stop_event.clear()
        sending = True
        sent_count = 0
        threading.Thread(target=send_emails, args=(sender_emails, email_password, recipient_emails, email_body, email_subject)).start()
        client.send_message("me", "تم بدء إرسال رسائل البريد الإلكتروني.")
    else:
        client.send_message("me", "إرسال رسائل البريد الإلكتروني قيد التشغيل بالفعل.")

if __name__ == "__main__":
    app.run()