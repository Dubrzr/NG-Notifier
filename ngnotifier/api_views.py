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
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = NGHostSerializer(host)
        return JSONResponse(serializer.data)

    return HttpResponse(status=404)


@csrf_exempt
def host_list(request):
    """
    Retrieve all NGHost.
    """
    if request.method == 'GET':
        hosts = NGHost.objects.all()
        serializer = NGHostSerializer(hosts, many=True)
        return JSONResponse(serializer.data)

    return HttpResponse(status=404)


@csrf_exempt
def group_list(request, host):
    """
    Retrieve all NGGroup.
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        hosts = NGGroup.objects.filter(host=host)
        serializer = NGGroupSerializer(hosts, many=True)
        return JSONResponse(serializer.data)

    return HttpResponse(status=404)


@csrf_exempt
def news_list(request, host, group):
    """
    Retrieve all NGNews.
    """
    try:
        host = NGHost.objects.get(host=host)
    except NGHost.DoesNotExist:
        print('here2')
        return HttpResponse(status=404)

    try:
        group = NGGroup.objects.get(host=host, name=group)
    except NGGroup.DoesNotExist:
        print('here')
        return HttpResponse(status=404)

    print('here3')
    if request.method == 'GET':
        news_list = NGNews.objects.filter(groups__in=[group])
        serializer = NGNewsSerializer(news_list, many=True)
        return JSONResponse(serializer.data)

    print('here4')
    return HttpResponse(status=404)
