from datetime import datetime
import re
import hashlib
import nntplib
from email.header import decode_header


def get_co(host, port, ssl, user, password, timeout):
    try:
        if ssl:
            co = nntplib.NNTP_SSL(host, port, user, password, timeout=timeout)
        else:
            co = nntplib.NNTP(host, port, user, password, timeout=timeout)
    except Exception as err:
        print("Can't connect to the host {}.".format(host))
        print("Error: {}".format(err))
        return None
    return co


def parse_nntp_date(str):
    # Parsing the date of the post
    try:
        return datetime.strptime(str, '%a, %d %b %Y %H:%M:%S')
    except:
        try:
            return datetime.strptime(str, '%a, %d %b %Y %H:%M:%S %z (%Z)')
        except:
            try:
                return datetime.strptime(str, '%a, %d %b %Y %H:%M:%S %Z')
            except:
                try:
                    return datetime.strptime(str, '%a, %d %b %Y %H:%M:%S %z')
                except:
                    try:
                        return datetime.strptime(str, '%d %b %Y %H:%M:%S %z')
                    except:
                        try:
                            return datetime.strptime(str, '%a, %d %b %Y %H:%M %z')
                        except:
                            try:
                                str_tmp = re.sub('(\+[0-2][0-9]:[0-5][0-9])', '', str)
                                return datetime.strptime(str_tmp, '%a, %d %b %Y %H:%M:%S %z (%Z)')
                            except:
                                print_fail(None, "Failed parsing date! (" + str + ')')
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
    contents, _ = decode_header(subject)[0]
    return get_decoded(contents)


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
        print(bcolors.HEADER + 'Host: ' + bcolors.ENDC, end=end, flush=False)
    elif type == 'group':
        print(bcolors.HEADER + '  Group: ' + bcolors.ENDC, end=end, flush=False)
    elif type == 'news':
        print(bcolors.HEADER + '    News: ' + bcolors.ENDC, end=end, flush=False)
    print(msg + '... ', end=end, flush=False)


def print_exists():
    print(
        bcolors.OKGREEN + 'Already exists!' + bcolors.ENDC
    )


def print_done():
    print(
        bcolors.OKGREEN + 'Added!' + bcolors.ENDC
    )


def print_fail(e, msg=None):
    print(
        bcolors.FAIL + 'Failed! ' + ((('(' + str(e) + ')') if e else '') if not msg else msg) + bcolors.ENDC
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
            [serializable_object(c, put_children, tab + 1) for c in
             [ch for ch in node.get_children()]
            ],
            key=lambda x: x['date'],
            reverse=True) if put_children and has_children else []
    }
    return obj