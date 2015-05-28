from datetime import datetime

from django.views.decorators.cache import never_cache
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
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
        except ValueError:
            return HttpResponse(status=400)
    else:
        e_date = datetime(1970, 1, 1, 00, 00)

    limit = int(request.GET.get('limit', '1000'))
    if limit < 1:
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
    print(serializer.to_representation(news))
    print(serializer.data)
    return JSONResponse(serializer.to_representation(news))