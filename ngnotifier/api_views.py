from datetime import datetime

from django.views.decorators.cache import never_cache
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from ngnotifier.utils import serializable_object
from rest_framework.decorators import api_view

from ngnotifier.models import NGHost, NGGroup, NGNews
from ngnotifier.api_serializers import NGHostSerializer, NGGroupSerializer,\
    NGNewsSerializer, NGNewsDetailSerializer
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
def news_detail(request, host, group, news_id):
    """
    Retrieve a news details with all answers
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        return HttpResponse(status=400)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        return HttpResponse(status=400)

    try:
        news = NGNews.objects.get(groups__in=[group], id=news_id)
    except NGGroup.DoesNotExist:
        return HttpResponse(status=400)

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

    n_list = []
    if author:
        a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                       email_from__regex=r'^.*' + term + '.*$')
        n_list = list(set(n_list) | set(a_list))
    if title:
        a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                       subject__regex=r'^.*' + term + '.*$')
        n_list = list(set(n_list) | set(a_list))
    if message:
        a_list = NGNews.objects.filter(groups__in=groups, date__lt=s_date,
                                       contents__regex=r'^.*' + term + '.*$')
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
