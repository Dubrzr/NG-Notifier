import smtplib
import json
from email.mime.text import MIMEText
from push_notifications.apns import apns_send_bulk_message
from push_notifications.gcm import gcm_send_bulk_message
from push_notifications.models import GCMDevice, APNSDevice

from pushbullet import PushBullet

from ngnotifier.settings import mail_conf as mail, FROM_ADDR, BOT_MSG
from pushbullet.errors import InvalidKeyError


def send_email(msg, subject, from_addr, to_addrs, type):
    if to_addrs == '':
        return 0

    msg = MIMEText(msg, type)
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['BCC'] = to_addrs

    try:
        if mail['ssl']:
            server = smtplib.SMTP_SSL(mail['host'], mail['port'], timeout=10)
        else:
            server = smtplib.SMTP(mail['host'], mail['port'], timeout=10)
    except Exception as err:
        print('Can\'t connect to the email server.')
        print("Error: {}".format(err))
        return 0

    try:
        server.login(mail['user'], mail['pass'])
    except:
        pass
    try:
        server.send_message(msg)
        server.quit()
        return len(to_addrs)
    except Exception as err:
        print("Can't send email...")
        print("Error: {}".format(err))

    return 0


def send_pushbullet(api_keys, subject, msg):
    count = 0

    for api_key in api_keys:
        try:
            pb = PushBullet(api_key)
            if not pb:
                continue
            pb.push_note(subject, msg)
            count += len(pb.devices)
        except InvalidKeyError:
            pass

    return count


def send_pushs(followers, group, id, subject):
    data = {
        'event_type': 'NEW_NEWS',
        'host': group.host.host,
        'newsgroup_id': group.id,
        'newsgroup': group.name,
        'news_id': id,
        'subject': subject
    }

    android_devices = GCMDevice.objects.filter(user__in=followers, active=1)
    ios_devices = APNSDevice.objects.filter(user__in=followers, active=1)

    android_devices.send_message(json.dumps(data))
    ios_devices.send_message(json.dumps(data))

    android_devices_after = GCMDevice.objects.filter(user__in=followers,
                                                     active=1)
    ios_devices_after = APNSDevice.objects.filter(user__in=followers,
                                                  active=1)
    return len(android_devices_after) + len(ios_devices_after)



def send_notif(new_news, ng_group):
    m = 0
    p = 0

    # If there is no followers for this group, don't send any notif
    followers = ng_group.followers.all()
    if followers.count() < 1:
        return 0, 0

    for ng_news in new_news:

        msg = ng_news.contents + ' ' + BOT_MSG\
                + '\nMessage sent in: ' + ' / '.join(
            [n.name for n in ng_news.groups.all()])\
                + '\nMessage author: ' + ng_news.email_from
        subject = ng_news.subject
        from_addr = FROM_ADDR

        m_to_addrs = ''
        p_api_keys = []

        for follower in followers:
            if follower.send_emails:
                # Add follower to emails' list
                m_to_addrs += ', ' if m_to_addrs != '' else ''
                m_to_addrs += follower.email

            if follower.send_pushbullets:
                # Add follower to pushbullet list
                p_api_keys.append(follower.pushbullet_api_key)

        m += send_email(msg,
                        subject,
                        from_addr,
                        m_to_addrs,
                        'plain')
        p += send_pushbullet(p_api_keys, subject, msg)
        p += send_pushs(followers, ng_group, ng_news.id, subject)
    return m, p
