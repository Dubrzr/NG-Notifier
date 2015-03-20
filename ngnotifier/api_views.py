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
        return HttpResponse(status=400)

    start_date = request.GET.get('start_date', '')

    if start_date != '':
        try:
            s_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S%z')
            s_date = s_date.replace(tzinfo=None)
        except ValueError:
            return HttpResponse(status=400)

    else:
        s_date = datetime(2000, 1, 1, 00, 00)

    limit = int(request.GET.get('limit', '1000'))
    if limit <1:
        return HttpResponse(status=400)

    if s_date > datetime.now():
        return HttpResponse(status=400)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        return HttpResponse(status=400)

    if request.method == 'GET':
        n_list = NGNews.objects\
                     .filter(groups__in=[group], date__gte=s_date, father='')\
                     .order_by('-date')[:limit]

        serializer = NGNewsSerializer(n_list, many=True)
        return JSONResponse(serializer.data)

    return HttpResponse(status=400)

@csrf_exempt
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
        except ValueError:
            return HttpResponse(status=400)
    else:
        e_date = datetime(2000, 1, 1, 00, 00)

    limit = int(request.GET.get('limit', '1000'))
    if limit <1:
        return HttpResponse(status=400)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        return HttpResponse(status=400)

    if request.method == 'GET':
        n_list = NGNews.objects\
                     .filter(groups__in=[group], date__lt=e_date, father='')\
                     .order_by('-date')[:limit]

        serializer = NGNewsSerializer(n_list, many=True)
        return JSONResponse(serializer.data)

    return HttpResponse(status=400)