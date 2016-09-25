import smtplib
import json
from email.mime.text import MIMEText
from ngnotifier.models import Log
from push_notifications.models import GCMDevice, APNSDevice

from pushbullet import PushBullet

from ngnotifier.settings import mail_conf as mail, FROM_ADDR, BOT_MSG
from pushbullet.errors import InvalidKeyError


def build_notif_msg(ng_news):
    return ng_news.contents + ' ' + BOT_MSG\
           + '\nMessage sent in: ' + ' / '.join(
        [n.name for n in ng_news.groups.all()])\
           + '\nMessage author: ' + ng_news.email_from

def send_email_notif(followers, ng_group, ng_news):

    to_addrs = ''

    users = []

    for follower in followers:
        if follower.send_emails:
            # Add follower to emails' list
            to_addrs += ', ' if to_addrs != '' else ''
            to_addrs += follower.email
            users.append(follower)

    if to_addrs == '':
        return

    msg = build_notif_msg(ng_news)

    send_email(to_addrs, ng_news.subject, msg, 'plain')

    for user in users:
        log = Log()
        log.type = 'N'
        log.group = ng_group
        log.user = user
        log.description = "Email notification (email=%s) (subject=%s)"\
                          % (user.email, ng_news.subject)
        log.save()


def send_email(to_addrs, subject, msg, mimetype):
    msg = MIMEText(msg,  mimetype)
    msg['Subject'] = subject
    msg['From'] = FROM_ADDR
    msg['BCC'] = to_addrs

    try:
        if mail['ssl']:
            server = smtplib.SMTP_SSL(mail['host'], mail['port'], timeout=10)
        else:
            server = smtplib.SMTP(mail['host'], mail['port'], timeout=10)
    except Exception as err:
        print('Can\'t connect to the email server.')
        print("Error: {}".format(err))
        return False

    try:
        server.login(mail['user'], mail['pass'])
    except:
        pass
    try:
        server.send_message(msg)
        server.quit()
    except Exception as err:
        print("Can't send email...")
        print("Error: {}".format(err))
        return False

    return True



def send_pushbullet(followers, ng_group, ng_news):
    msg = build_notif_msg(ng_news)

    for follower in followers:
        if follower.send_pushbullets:
            try:
                pb = PushBullet(follower.pushbullet_api_key)
                if not pb:
                    continue
                pb.push_note(ng_news.subject, msg)

            except InvalidKeyError:
                pass
            log = Log()
            log.type = 'N'
            log.group = ng_group
            log.user = follower
            log.description = "Pushbullet notification (api_key=%s) (subject=%s)"\
                              % (follower.pushbullet_api_key, ng_news.subject)
            log.save()


def send_pushs(followers, ng_group, ng_news):
    data = {
        'event_type': 'NEW_NEWS',
        'host': ng_group.host.host,
        'newsgroup_id': ng_group.id,
        'newsgroup': ng_group.name,
        'news_id': ng_news.id,
        'news_uid': ng_news.message_id,
        'subject': ng_news.subject,
        'author': ng_news.email_from,
        'creation_date': ng_news.date.strftime("%Y-%m-%dT%H:%M:%S%z")
    }

    android_devices = GCMDevice.objects.filter(user__in=followers, active=1)
    ios_devices = APNSDevice.objects.filter(user__in=followers, active=1)

    for android_device in android_devices:
        log = Log()
        log.type = 'N'
        log.group = ng_group
        log.user = android_device.user
        log.description = "Android notification (registration_id=%s) (subject=%s)"\
                          % (android_device.registration_id, ng_news.subject)
        log.save()

    for ios_device in ios_devices:
        log = Log()
        log.type = 'N'
        log.group = ng_group
        log.user = ios_device.user
        log.description = "iOs notification (registration_id=%s) (subject=%s)" \
                          % (ios_device.registration_id, ng_news.subject)
        log.save()


    android_devices.send_message(json.dumps(data))
    ios_devices.send_message(json.dumps(data))



def send_notif(new_news, ng_group):
    followers = ng_group.followers.all()

    # If there is no followers for this group, don't send any notification
    if followers.count() < 1:
        return

    for ng_news in new_news:
        send_email_notif(followers, ng_group, ng_news)
        send_pushbullet(followers, ng_group, ng_news)
        send_pushs(followers, ng_group, ng_news)