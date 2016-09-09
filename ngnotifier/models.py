from datetime import datetime
from itertools import chain
from _sha256 import sha224
from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction

from ngnotifier.utils import hash_over, parse_nntp_date, get_decoded,\
    print_done, print_exists, print_fail, print_msg, get_father,\
    properly_decode_header, bcolors, get_co
from push_notifications.models import APNSDevice, GCMDevice


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email.')
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password=password)
        user.is_admin = True
        user.is_active = True
        user.save(using=self.db)
        return user


class User(AbstractBaseUser):
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    email = models.EmailField('email address', max_length=254, unique=True)
    token = models.TextField()
    pushbullet_api_key = models.TextField(null=True)
    send_emails = models.BooleanField(default=True)
    send_pushbullets = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=datetime.now)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    signature = models.TextField(default='')
    anonymous = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            new_user_log = Log()
            new_user_log.type = 'NU'
            new_user_log.user = self
            new_user_log.save()
        else:
            super().save(*args, **kwargs)

    def get_groups_followed(self):
        return [d['followers_set'] for d in
                User.objects.values('followers_set').filter(id=self.id)]

    def switch_emails(self):
        self.send_emails = not self.send_emails
        self.save()

    def switch_pushbullets(self):
        if self.pushbullet_api_key:
            self.send_pushbullets = not self.send_pushbullets
            self.save()

    def switch_device(self, registration_id):
        devices = self.get_devices()
        for device in devices:
            if device.registration_id == registration_id:
                device.switch_active()
                break

    def add_ng_group(self, ng_group):
        ng_group.followers.add(self)
        ng_group.save()

    def del_ng_group(self, ng_group):
        ng_group.followers.remove(self)
        ng_group.save()

    def create_session(self, service, registration_id, device_name):
        try:
            if service == 'android':
                DeviceSession.objects.get(gcm_device__registration_id=registration_id).delete()
            else:
                DeviceSession.objects.get(apns_device__registration_id=registration_id).delete()
        except:
            pass
        session = DeviceSession()
        session.service = 'AN' if service == 'android' else 'IO'
        if service == 'android':
            gcm_device = GCMDevice(registration_id=registration_id, user=self, name=device_name)
            gcm_device.save()
            session.gcm_device = gcm_device
        else:
            apns_device = APNSDevice(registration_id=registration_id, user=self, name=device_name)
            apns_device.save()
            session.apns_device = apns_device
        session.save()
        return session

    def get_devices(self):
        devices = list(DeviceSession.objects.filter(gcm_device__user_id=self.id))
        devices += list(DeviceSession.objects.filter(apns_device__user_id=self.id))
        return devices


class DeviceSession(models.Model):
    session_key = models.CharField(max_length=60)
    ANDROID = 'AN'
    IOS = 'IO'
    SERVICE_CHOICES = (
        (ANDROID, 'Android'),
        (IOS, 'iOS'),
    )
    service = models.CharField(max_length=2, choices=SERVICE_CHOICES)
    gcm_device = models.ForeignKey(to='push_notifications.GCMDevice', null=True)
    apns_device = models.ForeignKey(to='push_notifications.APNSDevice', null=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.session_key = sha224(uuid4().hex.encode('utf-8')).hexdigest()
        return super(DeviceSession, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.service == 'AN':
            self.gcm_device.delete()
        else:
            self.apns_device.delete()
        return super(DeviceSession, self).delete(*args, **kwargs)

    def get_name(self):
        return self.gcm_device.name if self.service == 'AN'\
            else self.apns_device.name

    def get_registration_id(self):
        return self.gcm_device.registration_id if self.service == 'AN' \
            else self.apns_device.registration_id

    def get_user(self):
        return self.gcm_device.user if self.service == 'AN'\
            else self.apns_device.user

    def is_active(self):
        return self.gcm_device.active if self.service == 'AN'\
            else self.apns_device.active

    def switch_active(self):
        if self.service == 'AN':
            self.gcm_device.active = not self.is_active()
            self.gcm_device.save()
        else:
            self.apns_device.active = not self.is_active()
            self.apns_device.save()



def kinship_updater(news_list):
    if len(news_list) > 0:
        for news in news_list:
            if news.father != '':
                try:
                    father = NGNews.objects.get(message_id=news.father)
                    father.has_children = True
                    father.save()
                except Exception as e:
                    print(bcolors.FAIL, '      Failed! ', str(e), bcolors.ENDC)


class NGNews(models.Model):
    groups = models.ManyToManyField('NGGroup')
    hash = models.TextField(unique=True)
    subject = models.TextField()
    contents = models.TextField()
    email_from = models.TextField()
    message_id = models.TextField(unique=True)
    date = models.DateTimeField()
    lines = models.TextField()
    xref = models.TextField()
    references = models.TextField()
    father = models.TextField()
    has_children = models.NullBooleanField(default=None)
    bytes = models.TextField()
    nb_answers = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            new_news_log = Log()
            new_news_log.type = 'NN'
            new_news_log.news = self
            new_news_log.group = self.groups.first()
            new_news_log.save()
        else:
            super().save(*args, **kwargs)

    def get_host(self):
        for group in self.groups.first():
            return group.host.host

    def get_children(self):
        return NGNews.objects.filter(father=self.message_id)

    def get_groups(self):
        return [c.name for c in self.groups.all()]

    def add_group(self, group):
        self.groups.add(group)
        self.save()

    # Be careful to call this only once!
    def add_answer_count(self):
        if self.father != '':
            father = NGNews.objects.get(message_id=self.father)
            father.add_answer_count()
        self.nb_answers += 1
        self.save()


class NGGroup(models.Model):
    host = models.ForeignKey('NGHost')
    name = models.TextField()
    nb_news = models.IntegerField(default=0)
    nb_topics = models.IntegerField(default=0)
    followers = models.ManyToManyField(User, related_name="followers_set")

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
            new_group_log = Log()
            new_group_log.type = 'NG'
            new_group_log.group = self
            new_group_log.save()
        else:
            super().save(*args, **kwargs)

    @transaction.atomic
    def update_news(self, tmp_co=None, verbose=False):
        try:
            tmp_co = tmp_co if tmp_co else self.host.get_co()
        except Exception as err:
            if "423" in str(err):
                print("NGGroup {} does not exist anymore...".format(self.name))
                return []
            raise ConnectionError('Could not connect to the server, please '
                                  'check your connection ({}).'.format(err))
        try:
            # Getting infos & data from the given group
            _, _ , first, last, _ = tmp_co.group(self.name)
            # Sending a OVER command to get last_nb posts
            _, overviews = tmp_co.over((first, last))
        except Exception as err:
            if "411" in str(err) or "423" in str(err):
                print("NGGroup {} does not exist anymore...".format(self.name))
                return []
            raise ConnectionError('Could not connect to the server, please '
                                  'check your connection ({}).'.format(err))
        already_existing_news = []
        new_news_list = []
        for id, over in overviews:
            hash = hash_over(self.host.host, over)
            try:
                if verbose:
                    print_msg('news', properly_decode_header(over['subject']))
                try:
                    n = NGNews.objects.get(groups__in=[self], message_id=over['message-id'])
                    if verbose:
                        print_exists()
                    if n.hash != hash:
                        n.delete()
                        raise ObjectDoesNotExist()
                    # Check if the already existing news is in self group
                    if self not in n.groups.all():
                        already_existing_news.append(n)
                except ObjectDoesNotExist:
                    date = parse_nntp_date(over['date'])
                    _, info = tmp_co.body(over['message-id'])
                    contents = ''
                    for line in info[2]:
                        contents += get_decoded(line) + '\n'
                    try:
                        nn = NGNews()
                        nn.hash = hash
                        nn.subject = properly_decode_header(over['subject'])
                        nn.contents = contents
                        nn.email_from = properly_decode_header(over['from'])
                        nn.message_id = over['message-id']
                        nn.date = date
                        nn.lines = over[':lines']
                        nn.xref = over['xref']
                        nn.references = over['references']
                        nn.father = get_father(over['references'])
                        nn.bytes = over[':bytes']
                        new_news_list.append(nn)
                        if verbose:
                            print_done()
                    except Exception as e:
                        print_fail(e)
            except Exception as e:
                print_fail(e)
        for n in already_existing_news:
            n.add_group(self)
        for n in new_news_list:
            n.save()
            n.groups.add(self)
            n.save()
        self.nb_news += len(already_existing_news) + len(new_news_list)
        self.nb_topics = NGNews.objects.filter(groups__id=self.id, father='').count()
        self.save()
        return new_news_list

    def get_news(self):
        return NGNews.objects.filter(
            groups=self
        )

    def has_followers(self):
        return self.followers.all()

    def get_followers(self):
        return self.has_followers()

    def get_nb_topics(self):
        return NGNews.objects.filter(groups__in=[self], father='').count()


class NGHost(models.Model):
    host = models.TextField(unique=True)
    port = models.IntegerField(default=119)
    ssl = models.BooleanField(default=False)
    user = models.CharField(max_length=200, null=True)
    password = models.CharField(max_length=200, null=True)
    timeout = models.IntegerField(default=30)
    nb_notifs_sent = models.IntegerField(default=0)
    nb_groups = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def get_co(self):
        try:
            return get_co(self.host, self.port, self.ssl,
                          self.user, self.password, self.timeout)
        except Exception as err:
            raise ConnectionError('Could not connect to the server, please '
                                  'check your connection ({}).'.format(err))

    def get_ordered_groups(self):
        all_groups = NGGroup.objects.filter(
            host=self
        ).order_by('name')
        result_list = list(chain(all_groups.filter(nb_news__gt=0),
                                 all_groups.filter(nb_news=0)))
        return result_list

    @transaction.atomic
    def update_groups(self, groups=None, verbose=False):
        tmp_co = self.get_co()
        if groups is None or len(groups) == 0:
            _, grp_list = tmp_co.list()
            grp_list = [x.group for x in grp_list]
        else:
            grp_list = groups
        for group in grp_list:
            if verbose:
                print_msg('group', group)
            try:
                NGGroup.objects.get(
                    host=self,
                    name=group
                )
                if verbose:
                    print_exists()
            except ObjectDoesNotExist:
                try:
                    ng_group = NGGroup()
                    ng_group.host = self
                    ng_group.name = group
                    ng_group.save()
                    self.nb_groups += 1
                    self.save()
                    if verbose:
                        print_done()
                except Exception as e:
                    print_fail(e)


class Log(models.Model):
    TYPES = (
        ('NU', 'New user'),
        ('NN', 'New news'),
        ('NG', 'New group'),
        ('N', 'Notification'),
        ('P', 'Post'),
        ('UN', 'Update news'),
        ('UG', 'Update groups')
    )
    type = models.CharField(choices=TYPES, max_length=2, blank=False, default=None)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, null=True, default=None)
    news = models.ForeignKey(NGNews, null=True, default=None)
    group = models.ForeignKey(NGGroup, null=True, default=None)
    description = models.TextField(null=True)
