from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from ngnotifier.models import NGHost, NGGroup, NGNews
from ngnotifier.api_serializers import NGHostSerializer, NGGroupSerializer,\
    NGNewsSerializer
from ngnotifier.views import JSONResponse

@csrf_exempt
def host_detail(request, host_url):
    """
    Retrieve a NGHost.
    """
    try:
        host = NGHost.objects.get(host=host_url)
    except NGHost.DoesNotExist:
        return HttpResponse(status=400)

    if request.method == 'GET':
        serializer = NGHostSerializer(host)
        return JSONResponse(serializer.data)

    return HttpResponse(status=400)


@csrf_exempt
def host_list(request):
    """
    Retrieve all NGHost.
    """
    if request.method == 'GET':
        hosts = NGHost.objects.all()
        serializer = NGHostSerializer(hosts, many=True)
        return JSONResponse(serializer.data)

    return HttpResponse(status=400)


@csrf_exempt
def group_list(request, host):
    """
    Retrieve all NGGroup.
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        return HttpResponse(status=400)

    if request.method == 'GET':
        hosts = NGGroup.objects.filter(host=host)
        serializer = NGGroupSerializer(hosts, many=True)
        return JSONResponse(serializer.data)

    return HttpResponse(status=400)


@csrf_exempt
def news_list(request, host, group):
    """
    Retrieve all NGNews.
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        print('here2')
        return HttpResponse(status=400)

    start_date = request.GET.get('start_date', '')
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S%z')
    except:
        print('here58' + start_date)
        start_date = datetime(2000, 11, 21, 16, 30)

    start_date = start_date.replace(tzinfo=None)

    limit = int(request.GET.get('limit', '1000'))
    if limit <1:
        return HttpResponse(status=400)

    if start_date > datetime.now():
        return HttpResponse(status=400)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        print('here')
        return HttpResponse(status=400)

    print('here3')
    if request.method == 'GET':
        news_list = NGNews.objects.filter(groups__in=[group], date__gte=start_date).order_by('-date')[:limit]
        serializer = NGNewsSerializer(news_list, many=True)
        return JSONResponse(serializer.data)

    print('here4')
    return HttpResponse(status=400)

@csrf_exempt
def news_list_refresh(request, host, group):
    """
    Retrieve all NGNews.
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        print('here2')
        return HttpResponse(status=400)

    start_date = request.GET.get('start_date', '')
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S%z')
    except:
        start_date = datetime(2006, 11, 21, 16, 30)
    limit = int(request.GET.get('limit', '1000'))
    if limit <1:
        return HttpResponse(status=400)

    if start_date > datetime.now():
        return HttpResponse(status=400)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        print('here')
        return HttpResponse(status=400)

    print('here3')
    if request.method == 'GET':
        news_list = NGNews.objects.filter(groups__in=[group], date__gte=start_date).order_by('-date')[:limit]
        serializer = NGNewsSerializer(news_list, many=True)
        return JSONResponse(serializer.data)

    print('here4')
    return HttpResponse(status=400)