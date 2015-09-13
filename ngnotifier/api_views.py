from string import ascii_letters, digits
from django.shortcuts import get_object_or_404
from ngnotifier.settings import API_KEY
from random import choice
from _sha256 import sha224
from datetime import datetime
from uuid import uuid4

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ngnotifier.notifs import send_email
from ngnotifier import settings
from ngnotifier.utils import serializable_object, post_article
from push_notifications.models import GCMDevice, APNSDevice
from rest_framework.decorators import api_view
from ngnotifier.decorators import api_key_required, device_login_required

from ngnotifier.models import NGHost, NGGroup, NGNews, DeviceSession, User, Log
from ngnotifier.api_serializers import NGHostSerializer, NGGroupSerializer,\
    NGNewsSerializer, NGNewsDetailSerializer, NGNewsSerializerWithNames,\
    NGNewsSerializerWithNamesAndHost
from ngnotifier.views import JSONResponse

@never_cache
@csrf_exempt
@require_http_methods("GET")
def host_detail(request, host_url):
    """
    Retrieve a NGHost.
    """
    try:
        host = NGHost.objects.get(host=host_url)
    except NGHost.DoesNotExist:
        return HttpResponse(status=400)

    serializer = NGHostSerializer(host)
    return JSONResponse(serializer.data)


@never_cache
@csrf_exempt
@require_http_methods("GET")
def host_list(request):
    """
    Retrieve all NGHost.
    """
    hosts = NGHost.objects.all()
    serializer = NGHostSerializer(hosts, many=True)
    return JSONResponse(serializer.data)


@never_cache
@csrf_exempt
@require_http_methods("GET")
def group_list(request, host):
    """
    Retrieve all NGGroup.
    """
    hosts = NGGroup.objects.filter(host__host=host)\
        .order_by('name')
    serializer = NGGroupSerializer(hosts, many=True)
    return JSONResponse(serializer.data)


@never_cache
@csrf_exempt
@require_http_methods("GET")
def news_list(request, host, group):
    """
    Retrieve all NGNews.
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        return HttpResponse(status=400)

    start_date = request.GET.get('start_date', '')

    if start_date != '':
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S%z')
            s_date = s_date.replace(tzinfo=None)
        except ValueError:
            return HttpResponse(status=400)
    else:
        s_date = datetime.now()

    limit = int(request.GET.get('limit', '1000'))
    if limit < 1:
        return HttpResponse(status=400)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        return HttpResponse(status=400)

    n_list = NGNews.objects\
                 .filter(groups__in=[group], date__lt=s_date, father='')\
                 .order_by('-date')[:limit]

    serializer = NGNewsSerializer(n_list, many=True)
    return JSONResponse(serializer.data)


@never_cache
@csrf_exempt
@require_http_methods("GET")
def news_list_refresh(request, host, group):
    """
    Retrieve all NGNews.
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        return HttpResponse(status=400)

    end_date = request.GET.get('end_date', '')

    if end_date != '':
        try:
            e_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S%z')
            e_date = e_date.replace(tzinfo=None)
        except ValueError as e:
            return HttpResponse(status=400)
    else:
        e_date = datetime(1970, 1, 1, 00, 00)

    limit = request.GET.get('limit', '1000')
    if limit == '' or not limit.isdigit():
        return HttpResponse(status=400)
    limit = int(limit)
    if not limit > 0:
        return HttpResponse(status=400)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        return HttpResponse(status=400)

    n_list = NGNews.objects\
                 .filter(groups__in=[group], date__gt=e_date, father='')\
                 .order_by('-date')[:limit]

    serializer = NGNewsSerializer(n_list, many=True)
    return JSONResponse(serializer.data)


@never_cache
@csrf_exempt
@api_view(['GET'])
def news_detail(request, news_id):
    """
    Retrieve a news details with all answers
    """
    news = None
    while True:
        try:
            news = NGNews.objects.get(id=news_id)
        except NGGroup.DoesNotExist:
            return HttpResponse(status=400)
        if news.father == '':
            break
        else:
            try:
                father = NGNews.objects.get(message_id=news.father)
                news_id = father.id
            except:
                return HttpResponse(status=500)

    serializer = NGNewsDetailSerializer(news)
    return JSONResponse(serializer.to_representation(news))

@never_cache
@csrf_exempt
@api_view(['GET'])
def search(request, host=None, group=None):

    term = request.GET.get('term', '')
    if len(term) < 2:
        return HttpResponse(status=400)

    limit = request.GET.get('limit', '1000')
    if limit == '' or not limit.isdigit():
        return HttpResponse(status=400)
    limit = int(limit)
    if not limit > 0:
        return HttpResponse(status=400)

    start_date = request.GET.get('start_date', '')
    if start_date != '':
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S%z')
            s_date = s_date.replace(tzinfo=None)
        except ValueError:
            return HttpResponse(status=400)
    else:
        s_date = datetime(2099, 1, 1, 00, 00)

    author = request.GET.get('author', 'false')
    author = True if author == '' else (True if author == 'true' else False)
    title = request.GET.get('title', 'false')
    title = True if title == '' else (True if title == 'true' else False)
    message = request.GET.get('message', 'false')
    message = True if message == '' else (True if message == 'true' else False)

    if not author and not title and not message:
        author = True
        title = True
        message = True
    
    if host and group:
        try:
            host = NGHost.objects.get(host=host)
            groups = [NGGroup.objects.get(host=host, name=group)]
        except:
            return HttpResponse(status=404)
    elif host:
        try:
            host = NGHost.objects.get(host=host)
            groups = NGGroup.objects.filter(host=host)
        except:
            return HttpResponse(status=404)
    else:
        groups = NGGroup.objects.all()


    case = request.GET.get('case', 'false')
    case = True if (case == '') else (True if case == 'true' else False)

    n_list = []
    if author:
        if case:
            a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                           email_from__regex=r'^.*' + term + '.*$')
        else:
            a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                           email_from__iregex=r'^.*' + term + '.*$')
        n_list = list(set(n_list) | set(a_list))
    if title:
        if case:
            a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                            subject__regex=r'^.*' + term + '.*$')
        else:
            a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                           subject__iregex=r'^.*' + term + '.*$')
        n_list = list(set(n_list) | set(a_list))
    if message:
        if case:
            a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                           contents__regex=r'^.*' + term + '.*$')
        else:
            a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                           contents__iregex=r'^.*' + term + '.*$')
        n_list = list(set(n_list) | set(a_list))

    n_list.sort(key=lambda x: x.date, reverse=True)

    n_list = n_list[:limit]

    names = request.GET.get('names', 'false')
    names = True if names == '' else (True if names == 'true' else False)

    if names:
        if host:
            serializer = NGNewsSerializerWithNames(n_list, many=True)
        else:
            serializer = NGNewsSerializerWithNamesAndHost(n_list, many=True)
    else:
        serializer = NGNewsSerializer(n_list, many=True)

    web_render = request.GET.get('web_render', False) != False
    if web_render:
        data = [serializable_object(n, light=True) for n in n_list]
        return JsonResponse(data, safe=False)
    else:
        return JSONResponse(serializer.data)


@csrf_exempt
@api_view(['POST'])
@api_key_required
def login_phone(request):

    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    service = request.POST.get('service', '')
    registration_id = request.POST.get('registration_id', '')
    device_name = request.POST.get('device_name', '')

    if username == '' or password == '' or \
        service == '' or registration_id == '' or device_name == '':
        return HttpResponse(status=404)

    if not (service == 'android' or service == 'ios'):
        return JsonResponse({'error': 3, 'message': "The service should be either 'android' or 'ios'"}, safe=False, status=403)

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            session = user.create_session(service, registration_id, device_name)

            data = {
                'error': 0,
                'notifs': {
                    'email': user.send_emails,
                    'pushbullet': user.send_pushbullets,
                    'pushbullet_api_key': user.pushbullet_api_key,
                    'devices': [
                        {
                            'id': d.id,
                            'name': d.get_name(),
                            'active': d.is_active(),
                            'type': 'android' if d.service == 'AN' else 'ios'

                        } for d in user.get_devices()
                    ] if user.get_devices() else []
                },
                'session_key': session.session_key
            }
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 2, 'message': "You must first confirm your account"}, safe=False, status=403)

    return JsonResponse({'error': 1, 'message': "This account does not exist / the specified password is incorrect"}, safe=False, status=403)

@csrf_exempt
@api_view(['GET'])
@api_key_required
@device_login_required
def logout_phone(request, device_session):
    device_session.delete()
    return HttpResponse(status=200)


@csrf_exempt
@api_view(['GET'])
@api_key_required
@device_login_required
def group_subscriptions(request, device_session, host):
    user = device_session.get_user()
    try:
        host = NGHost.objects.get(host=host)
        groups = NGGroup.objects.filter(host=host)
    except ObjectDoesNotExist:
        return HttpResponse(status=404)
    data = [{'name': g.name, 'subscribed': (user in g.followers.all())} for g in groups.all()]
    return JsonResponse(data, safe=False, status=200)


@csrf_exempt
@api_view(['POST'])
@api_key_required
def register_phone(request):

    username = request.POST.get('username', '')
    password = request.POST.get('password', '')

    if username == '' or password == '':
        return HttpResponse(status=404)

    try:
        validate_email(username)
    except ValidationError:
        data = {
            "error" : 2,
            "message" : "Invalid username format (must be a valid email address)"
        }
        return JsonResponse(data, safe=False, status=400)

    try:
        User.objects.get(email=username)
        data = {
            "error" : 1,
            "message" : "This mail is already used in an account"
        }
        return JsonResponse(data, safe=False, status=400)
    except ObjectDoesNotExist:
        token = sha224(uuid4().hex.encode('utf-8')).hexdigest()
        new_user = User()
        new_user.token = token
        new_user.email = username
        new_user.set_password(password)
        new_user.save()

        context = {
            'user': new_user,
            'token': token,
            'site_url': settings.SITE_URL
        }
        html_content = render_to_string(
            'email/token.html',
            context,
            context_instance=RequestContext(request)
        )
        if send_email(html_content, 'NG Notifier',
                      settings.FROM_ADDR, new_user.email, 'html'):
            return HttpResponse(status=200)

        return HttpResponse(status=500)


@csrf_exempt
@api_view(['POST'])
@api_key_required
def forgot_password_phone(request):

    username = request.POST.get('username', '')

    if username == '':
        return HttpResponse(status=200)

    try:
        token = sha224(uuid4().hex.encode('utf-8')).hexdigest()
        user = User.objects.get(email=username)
        user.token = token
        user.save()
        context = {
            'user': user,
            'token': token,
            'site_url': settings.SITE_URL
        }
        html_content = render_to_string(
            'email/forgot_password.html',
            context,
            context_instance=RequestContext(request)
        )
        if send_email(html_content, 'NG Notifier',
                      settings.FROM_ADDR, user.email, 'html'):
            return HttpResponse(status=200)
    except ObjectDoesNotExist:
        return HttpResponse(status=200)



@csrf_exempt
@api_view(['POST'])
@api_key_required
def subscribe_notifications(request):

    service = request.POST.get('service', '')
    registration_id = request.POST.get('registration_id', '')
    host = request.POST.get('host', '')
    newsgroup = request.POST.get('newsgroup', '')
    newsgroup_list = newsgroup.split(sep=',')

    if service == '' or registration_id == '' or host =='' or newsgroup == '':
        return HttpResponse(status=404)

    if not (service == 'android' or service == 'ios'):
        return JsonResponse({'error': 0, 'message': "The service should be either 'android' or 'ios'"}, safe=False, status=403)

    host_obj = get_object_or_404(NGHost, host=host)

    # Optional login
    session_key = request.META.get('HTTP_SESSION', '')
    try:
        session = DeviceSession.objects.get(session_key=session_key)
    except ObjectDoesNotExist:
        # Try to find if an anonymous user already exists for this device
        try:
            if service == 'android':
                device = GCMDevice.objects.get(registration_id=registration_id)
                session = DeviceSession.objects.get(gcm_device=device)
            else:
                device = APNSDevice.objects.get(registration_id=registration_id)
                session = DeviceSession.objects.get(apns_device=device)
        except ObjectDoesNotExist:
            # Else create a temporary anonymous user
            random = ''.join([choice(ascii_letters + digits) for n in range(32)])
            anonymous = User()
            anonymous.email = random + '@anonymo.us'
            anonymous.is_active = True
            anonymous.anonymous = True
            anonymous.save()
            session = anonymous.create_session(service, registration_id, "anonymous")

    user = session.get_user()

    added_list = []

    for newsgroup in newsgroup_list:
        if newsgroup == '':
            continue

        group_obj = get_object_or_404(NGGroup, name=newsgroup, host=host_obj)

        if not user in group_obj.followers.all():
            user.add_ng_group(group_obj)
            added_list.append(newsgroup)

    return JsonResponse({'added': added_list}, safe=False, status=200)



@csrf_exempt
@api_view(['POST'])
@api_key_required
def unsubscribe_notifications(request):

    service = request.POST.get('service', '')
    registration_id = request.POST.get('registration_id', '')
    host = request.POST.get('host', '')
    newsgroup = request.POST.get('newsgroup', '')
    newsgroup_list = newsgroup.split(sep=',')

    if service == '' or registration_id == '' or host =='' or newsgroup == '':
        return HttpResponse(status=404)

    if not (service == 'android' or service == 'ios'):
        return JsonResponse({'error': 0, 'message': "The service should be either 'android' or 'ios'"}, safe=False, status=403)

    host_obj = get_object_or_404(NGHost, host=host)

    # Optional login
    session_key = request.META.get('HTTP_SESSION', '')
    try:
        session = DeviceSession.objects.get(session_key=session_key)
    except ObjectDoesNotExist:
        # Try to find if an anonymous user already exists for this device
        try:
            if service == 'android':
                device = GCMDevice.objects.get(registration_id=registration_id)
                session = DeviceSession.objects.get(gcm_device=device)
            else:
                device = APNSDevice.objects.get(registration_id=registration_id)
                session = DeviceSession.objects.get(apns_device=device)
        except ObjectDoesNotExist:
            # Else create a temporary anonymous user
            random = ''.join([choice(ascii_letters + digits) for n in range(32)])
            anonymous = User()
            anonymous.email = random + '@anonymo.us'
            anonymous.is_active = True
            anonymous.anonymous = True
            anonymous.save()
            session = anonymous.create_session(service, registration_id, "anonymous")

    user = session.get_user()

    remove_list = []
    for newsgroup in newsgroup_list:
        if newsgroup == '':
            continue

        group_obj = get_object_or_404(NGGroup, name=newsgroup, host=host_obj)

        if user in group_obj.followers.all():
            user.del_ng_group(group_obj)
            remove_list.append(newsgroup)

    return JsonResponse({'removed': remove_list}, safe=False, status=200)


@csrf_exempt
@api_view(['POST'])
@api_key_required
@device_login_required
def post_phone(request):

    host = request.POST.getlist('host')
    groups = request.POST.getlist('groups')
    subject = request.POST.get('subject')
    name = request.POST.get('name')
    email = request.POST.get('email')
    contents = request.POST.get('contents')

    if host == '' or groups == '' or subject == '' or name == '' or email == ''\
            or contents == '':
        return HttpResponse(status=404)

    try:
        groups = [NGGroup.objects.get(name=group, host__host=host) for group in
                  groups.split(sep=',')]
    except:
        return HttpResponse(status=400)

    if post_article(name, email, groups, subject, contents):
        post_log = Log()
        post_log.type = 'P'
        post_log.date = datetime.now()
        post_log.user = request.user
        post_log.description = subject + ' ' + name
        post_log.save()
        return HttpResponse(status=200)

    return HttpResponse(status=500)