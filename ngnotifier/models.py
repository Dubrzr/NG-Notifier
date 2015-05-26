from datetime import datetime
from itertools import chain

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
    is_admin = models.BooleanField(
        default=False
    )

    def get_groups_followed(self):
        return [d['followers_set'] for d in
                User.objects.values('followers_set').filter(id=self.id)]

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


def kinship_updater(new_news_list):
    if len(new_news_list) > 0:
        for news in new_news_list:
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

    def get_children(self):
        return NGNews.objects.filter(father=self.message_id)

    def get_groups(self):
        return [c.name for c in self.groups.all()]


class Log(models.Model):
    TYPES = (
        ('NN', 'New news'),
        ('N', 'Notification'),
        ('P', 'Post')
    )
    type = models.CharField(choices=TYPES, max_length=2)
    date = models.DateTimeField()
    user = models.ForeignKey(User, default=None)
    news = models.ForeignKey(NGNews, default=None)
    description = models.TextField(null=True)



class NGHost(models.Model):
    host = models.TextField(unique=True)
    port = models.IntegerField(default=119)
    ssl = models.BooleanField(default=False)

    user = models.TextField(default=None)
    password = models.TextField(default=None)

    timeout = models.IntegerField(default=30)
    nb_notifs_sent = models.IntegerField(default=0)

    # known_news = models.ManyToManyField(NGNews)
    nb_groups = models.IntegerField(default=0)
    def add_news(self, news):
        #self.known_news.add(news)
        self.save()

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

    def update_groups(self, groups=None, check_news=True, check_kinship=False,
                      verbose=True):
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
        if check_kinship:
            kinship_updater(new_news_list)


class NGGroup(models.Model):
    host = models.ForeignKey(NGHost)
    name = models.TextField()
    nb_news = models.IntegerField(default=0)

    followers = models.ManyToManyField(User, related_name="followers_set")

    def update_news(self, tmp_co=None, verbose=True):
        try:
            tmp_co = tmp_co if tmp_co else self.host.get_co()
        except Exception as err:
            raise ConnectionError('Could not connect to the server, please '
                                  'check your connection ({}).'.format(err))
        try:
            # Getting infos & data from the given group
            _, _, first, last, _ = tmp_co.group(self.name)
            # Sending a OVER command to get last_nb posts
            _, overviews = tmp_co.over((first, last))
        except Exception as err:
            raise ConnectionError('Could not connect to the server, please '
                                  'check your connection ({}).'.format(err))
        already_existing_news = []
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
                    # Check if the already existing news is in self group
                    if not self in n.groups.all():
                        already_existing_news.append(n)
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
                        new_news_list.append(new_news)
                        if verbose:
                            print_done()
                    except Exception as e:
                        print_fail(e)
            except Exception as e:
                print_fail(e)
        for n in already_existing_news:
            n.groups.add(self)
            n.save()
        for n in new_news_list:
            n.save()
            n.groups.add(self)
            n.save()
        self.nb_news += len(already_existing_news) + len(new_news_list)
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