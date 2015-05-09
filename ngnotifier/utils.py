from datetime import datetime
import re
import hashlib
import nntplib
from email.header import decode_header, make_header
from ngnotifier.settings import hosts


def get_co(host, port, ssl, user, password, timeout):
    try:
        if ssl:
            co = nntplib.NNTP_SSL(host, port, user, password, timeout=timeout)
        else:
            co = nntplib.NNTP(host, port, user, password, timeout=timeout)
    except Exception as err:
        raise ConnectionError('Could not connect to the server, please, check '
                         'your connection ({}).'.format(err))
    return co


def parse_nntp_date(str):
    # Parse the date of a post

    # First try all registered possible formats
    possible_formats = [
        '%a, %d %b %Y %H:%M:%S',
        '%a, %d %b %Y %H:%M:%S %z (%Z)',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S %z',
        '%d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M %z'
    ]
    for f in possible_formats:
        try:
            return datetime.strptime(str, f)
        except:
            pass

    # If it failed, try another one by deleting incorrect TZ time
    try:
        str_tmp = re.sub('(\+[0-2][0-9]:[0-5][0-9])', '', str)
        return datetime.strptime(str_tmp, '%a, %d %b %Y %H:%M:%S %z (%Z)')
    except:
        # If it didn't worked either, just return current date!
        print_fail(None, 'Failed parsing date! (' + str + ')')
        return datetime.now()


def get_father(references):
    try:
        return references.split()[-1]
    except Exception:
        return ''


def get_encoded(str):
    try:
        str = str.encode('utf-8')
    except:
        try:
            str = str.encode('iso-8859-15', 'surrogateescape')
        except:
            try:
                str = str.encode("windows-1252")
            except Exception as err:
                print('Error occured during encoding process.')
                print('Error: {}'.format(err))
                return None
    return str


def get_decoded(str):
    try:
        str = str.decode('utf-8')
    except:
        try:
            str = str.decode('iso-8859-15', 'surrogateescape')
        except:
            try:
                str = str.decode("windows-1252")
            except Exception as err:
                # print('Error occured during decoding process.')
                # print('Error: {}'.format(err))
                return str
    return str


def properly_decode_header(subject):
    contents = make_header(decode_header(subject))
    return str(contents)


def hash_over(over):
    try:
        str = over['subject'] + over['xref'] + over['message-id']
    except Exception as err:
        print('Error occured during getting keys of over dictionary.')
        print('Error: {}'.format(err))
        return None

    str = get_encoded(str)
    if str is None:
        return None

    return hashlib.sha1(str).hexdigest()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_msg(type, msg, end=''):
    if type == 'host':
        print(bcolors.HEADER, 'Host: ', bcolors.ENDC, end=end, flush=False)
    elif type == 'group':
        print(bcolors.HEADER, '  Group: ', bcolors.ENDC, end=end, flush=False)
    elif type == 'news':
        print(bcolors.HEADER, '    News: ', bcolors.ENDC, end=end, flush=False)
    print(msg, '... ', end=end, flush=False)


def print_exists():
    print(
        bcolors.OKGREEN, 'Already exists!', bcolors.ENDC
    )


def print_done():
    print(
        bcolors.OKGREEN, 'Added!', bcolors.ENDC
    )


def print_fail(e, msg=None):
    print(
        bcolors.FAIL, 'Failed! ',
        ((('(' + str(e) + ')') if e else '') if not msg else msg),
        bcolors.ENDC
    )


def print_rec(data):
    if data:
        print(data['display-name'])
        [print_rec(d) for d in data['children']]


def ng_news_has_children(ng_news):
    if ng_news.has_children is None:
        children = ng_news.get_children()
        ng_news.has_children = len(children) > 0
        ng_news.save()
    return ng_news.has_children


def serializable_object(node, put_children=False, tab=0):
    has_children = ng_news_has_children(node)
    obj = {
        'id': node.id,
        'name': node.subject,
        'date': node.date,
        'display-name': node.date.strftime('<b>%d-%m-%y %H:%M</b> | ')
                        + ('&nbsp;' * 8 * (tab - 1) if tab > 1 else '')
                        + ('^---' if tab > 0 else '')
                        + ('● ' if has_children > 0 else '○ ') + node.subject
                        + ' <b>' + node.email_from + '</b>',
        'children': sorted(
            [serializable_object(c, put_children, tab + 1) for c in node.get_children()],
            key=lambda x: x['date'],
            reverse=True
        ) if put_children and has_children else []
    }
    return obj


def build_article(name, email, groups, subject, contents):
    res = ''
    res += 'From: ' + name + ' <' + email + '>' + '\r\n'
    res += 'Newsgroups: ' + ",".join(groups) + '\r\n'
    res += 'Subject: ' + subject + '\r\n'
    res += 'Date: ' + datetime.now().strftime("%a, %d %b %Y %H:%M:%S") + '\r\n'
    res += '\r\n'
    res += contents + '\r\n'
    return res.encode('utf-8')


def post_article(name, email, groups, subject, contents):
    for group in groups:
        settings = hosts[group.host.host]
        try:
            if settings['ssl']:
                co = nntplib.NNTP_SSL(settings['host'], settings['port'],
                                      settings['user'], settings['pass'],
                                      timeout=settings['timeout'])
            else:
                co = nntplib.NNTP(settings['host'], settings['port'],
                                  settings['user'], settings['pass'],
                                  timeout=settings['timeout'])
        except Exception:
            return False
        print(co.post(build_article(name, email, [group.name], subject, contents)))
        return True
