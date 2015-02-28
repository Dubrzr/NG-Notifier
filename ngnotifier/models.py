from datetime import datetime
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from ngnotifier.utils import hash_over, parse_nntp_date, get_decoded,\
    print_done, print_exists,\
    print_fail, print_msg, get_father,\
    properly_decode_header, bcolors, get_co


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError('Users must have an email.')
        user = self.model(email=email)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email, password=password)
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    email = models.EmailField(
        'email address',
        max_length=254,
        unique=True)

    token = models.TextField()

    pushbullet_api_key = models.TextField(null=True)

    send_emails = models.BooleanField(default=True)
    send_pushbullets = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=datetime.now())

    is_active = models.BooleanField(
        default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            pass
        super().save(*args, **kwargs)

    @staticmethod
    def __tag__():
        return 'User'

    def switch_emails(self):
        self.send_emails = not self.send_emails
        self.save()

    def switch_pushbullets(self):
        if self.pushbullet_api_key:
            self.send_pushbullets = not self.send_pushbullets
            self.save()

    def add_ng_group(self, ng_group):
        ng_group.followers.add(self)
        ng_group.save()


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

    def get_children(self):
        return NGNews.objects.filter(father=self.message_id)


class NGHost(models.Model):
    host = models.TextField(unique=True)
    port = models.IntegerField(max_length=65535, default=119)
    ssl = models.BooleanField(default=False)

    user = models.TextField(null=True, default=None)
    password = models.TextField(null=True, default=None)

    timeout = models.IntegerField(max_length=120, default=30)
    nb_notifs_sent = models.IntegerField(default=0)

    known_news = models.ManyToManyField(NGNews)
    nb_groups = models.IntegerField(default=0)

    def add_news(self, news):
        self.known_news.add(news)
        self.save()

    def get_co(self):
        return get_co(self.host, self.port, self.ssl,
                            self.user, self.password, self.timeout)

    def get_groups(self):
        return NGGroup.objects.filter(
            host=self
        )

    def update_groups(self, groups=None, check_news=True, verbose=True):
        tmp_co = self.get_co()
        if groups is None or len(groups) == 0:
            _, list = tmp_co.list()
            list = [x.group for x in list]
        else:
            list = groups
        new_news_list = []
        for group in list:
            if verbose:
                print_msg('group', group)
            try:
                ng_group = NGGroup.objects.get(
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
                    ng_group = None
                    print_fail(e)
            if check_news and ng_group:
                new_news_list += ng_group.update_news(tmp_co, verbose=verbose)
        if verbose and len(new_news_list) > 0:
            print('    Updating kinships for {} host.'.format(self.host))
        for news in new_news_list:
            if news.father != '':
                try:
                    father = NGNews.objects.get(message_id=news.father)
                    father.has_children = True
                    father.save()
                except Exception as e:
                    print(
                        bcolors.FAIL + '      Failed! ' + str(e) + bcolors.ENDC
                    )


class NGGroup(models.Model):
    host = models.ForeignKey(NGHost)
    name = models.TextField()
    nb_news = models.IntegerField(default=0)

    followers = models.ManyToManyField(User)

    def update_news(self, tmp_co=None, verbose=True):
        tmp_co = tmp_co if tmp_co else self.host.get_co()
        try:
            # Getting infos & data from the given group
            _, _, first, last, _ = tmp_co.group(self.name)
            # Sending a OVER command to get last_nb posts
            _, overviews = tmp_co.over((first, last))
        except Exception as err:
            print("Can't get news from {} group.".format(self.name))
            print("Error: {}".format(err))
            return
        new_news_list = []
        for id, over in overviews:
            hash = hash_over(over)
            try:
                if verbose:
                    print_msg('news', properly_decode_header(over['subject']))
                try:
                    n = NGNews.objects.get(
                        hash=hash
                    )
                    if verbose:
                        print_exists()
                    if not self in n.groups.all():
                        n.groups.add(self)
                        n.save()
                except ObjectDoesNotExist:
                    date = parse_nntp_date(over['date'])
                    _, info = tmp_co.body(over['message-id'])
                    result = ''
                    for line in info[2]:
                        result += get_decoded(line) + '\n'
                    try:
                        new_news = NGNews()
                        new_news.hash = hash
                        new_news.subject = properly_decode_header(over[
                            'subject'])
                        new_news.contents = result
                        new_news.email_from = properly_decode_header(
                            over['from'])
                        new_news.message_id = over['message-id']
                        new_news.date = date
                        new_news.lines = over[':lines']
                        new_news.xref = over['xref']
                        new_news.references = over['references']
                        new_news.father = get_father(over['references'])
                        new_news.bytes = over[':bytes']
                        new_news.save()
                        new_news.groups.add(self)
                        new_news.save()
                        new_news_list.append(new_news)
                        if verbose:
                            print_done()
                    except Exception as e:
                        print_fail(e)
            except Exception as e:
                print_fail(e)
        self.nb_news += len(new_news_list)
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