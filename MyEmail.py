import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
from MyRedis import RedisSingleton
from config import REDIS_CONFIG, EMAIL_CONFIG
redis_conn = RedisSingleton(host=REDIS_CONFIG['host'], password=REDIS_CONFIG['password'], db=REDIS_CONFIG['db']).get_connection()

body_head = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }
        .container {
            background-color: #ffffff;
            margin: 50px auto;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            max-width: 600px;
        }
        .header {
            text-align: center;
            padding: 10px 0;
            border-bottom: 1px solid #eaeaea;
        }
        .header h1 {
            margin: 0;
            color: #333333;
        }
        .content {
            margin: 20px 0;
            line-height: 1.6;
            color: #333333;
        }
        .content p {
            margin: 0;
        }
        .footer {
            text-align: center;
            padding: 10px 0;
            border-top: 1px solid #eaeaea;
            font-size: 12px;
            color: #888888;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>邮件主题</h1>
        </div>
        <div class="content">
            <p>亲爱的用户，</p>
            <p>这是一封具有验证码信息并且风格简洁科技的邮件。</p>
"""
body_footer = """
            <p>感谢您的阅读！</p>
        </div>
        <div class="footer">
            <p>© 2024 公司名称. 保留所有权利。</p>
        </div>
    </div>
</body>
</html>
"""


def send_email(receiver_email, subject, auth_code):
    receiver_emails = [receiver_email]
    message = MIMEMultipart("alternative")
    message["From"] = EMAIL_CONFIG['sender_email']
    message["To"] = ", ".join(receiver_emails)
    message["Subject"] = subject
    message.attach(MIMEText(body_head + f"<p>您的有验证码是: {auth_code}</p>" + body_footer, "html"))
    context = ssl.create_default_context()
    # 发送邮件
    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['port'], context=context) as server:
            server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
            server.sendmail(EMAIL_CONFIG['sender_email'], receiver_emails, message.as_string())
        if redis_conn.exists(f"email:{receiver_email}"):
            redis_conn.delete(f"email:{receiver_email}")
        redis_conn.setex(f"email:{receiver_email}", 60 * 5, auth_code)
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False
