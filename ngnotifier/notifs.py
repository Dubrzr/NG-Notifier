import smtplib
from ngnotifier.settings import mail_conf as mail, FROM_ADDR, BOT_TAG, BOT_MSG
from pushbullet import PushBullet
from email.mime.text import MIMEText


def send_email(msg, subject, from_addr, to_addrs, type):
    msg = MIMEText(msg, type)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addrs
    try:
        if mail['ssl']:
            server = smtplib.SMTP_SSL(mail['host'],mail['port'], timeout=10)
        else:
            server = smtplib.SMTP(mail['host'], mail['port'], timeout=10)
    except Exception as err:
        print('Can\'t connect to the email server.')
        print("Error: {}".format(err))
        return False

    try:
        server.login(mail['user'], mail['pass'])
        server.send_message(msg)
        server.quit()
    except Exception as err:
        print("Can't send email...")
        print("Error: {}".format(err))
        return False
    return True


def send_pushbullet(api_key, devices, subject, msg):
    pb = PushBullet(api_key)
    if not pb:
        return False
    for device in pb.devices:
        device.push_note(subject, msg)
        return True


def send_notif(new_news, ng_group):
    m = 0
    p = 0
    followers = ng_group.followers.all()
    if followers.count() > 0:
        for ng_news in new_news:

            m_msg = ng_news.contents + ' ' + BOT_MSG
            m_subject = ng_news.subject + ' ' + BOT_TAG
            m_from_addr = FROM_ADDR

            m_to_addrs = ''

            for follower in followers:
                if follower.send_emails:
                    m_to_addrs += ', ' if m_to_addrs != '' else ''
                    m_to_addrs += follower.email
                    m += 1
                if follower.send_pushbullets:
                    send_pushbullet(
                        follower.pushbullet_api_key,
                        None,
                        m_subject,
                        m_msg)
                    p += 1
            if m_to_addrs != '':
                send_email(
                    m_msg,
                    m_subject,
                    m_from_addr,
                    m_to_addrs,
                    'text'
                )
    return m, p
