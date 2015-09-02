from _sha256 import sha224
from datetime import datetime
from uuid import uuid4

from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ngnotifier.utils import serializable_object
from rest_framework.decorators import api_view

from ngnotifier.models import NGHost, NGGroup, NGNews, User
from ngnotifier.api_serializers import NGHostSerializer, NGGroupSerializer,\
    NGNewsSerializer, NGNewsDetailSerializer
from ngnotifier.views import JSONResponse
from ngnotifier.settings import API_KEY


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
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        return HttpResponse(status=400)

    hosts = NGGroup.objects.filter(host=host)\
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

    print(str(case))
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

    serializer = NGNewsSerializer(n_list, many=True)

    web_render = request.GET.get('web_render', False) != False
    if web_render:
        data = [serializable_object(n, light=True) for n in n_list]
        return JsonResponse(data, safe=False)
    else:
        return JSONResponse(serializer.data)


@api_view(['GET'])
def login_phone(request):
    if API_KEY == '':
        return HttpResponse(status=500)

    api_key = request.GET.get('key', '')
    login = request.GET.get('login', '')
    password = request.GET.get('password', '')

    if api_key == '' or login == '' or password == '':
        return HttpResponse(status=404)

    if api_key != API_KEY:
        return HttpResponse(status=404)

    try:
        user = User.objects.get(email=login)
    except:
        return HttpResponse(status=404)

    if not user.is_active:
        return JsonResponse({'error': 2, 'message': "You must first confirm your account"}, safe=False, status=403)

    if not user.check_password(password):
        return JsonResponse({'error': 1, 'message': "This account does not exist / specified password is incorrect"}, safe=False, status=403)

    token = sha224(uuid4().hex.encode('utf-8')).hexdigest()
    user.token_phone = token
    user.save()


    data = {
        'error': 0,
        'token': token,
        'notifs': {
            'email': user.send_emails,
            'pushbullet': user.send_pushbullets,
            'pushbullet_api_key': user.pushbullet_api_key,
            'devices': []
        }
    }

    return JsonResponse(data, safe=False)

