from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404, JsonResponse, HttpResponseRedirect,\
    HttpResponse
from django.template.loader import render_to_string
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse as rf_reverse
from django.contrib.auth import logout

from ngnotifier import settings
from ngnotifier.forms import CaptchaForm, SettingsForm
from ngnotifier.models import NGHost, NGGroup, NGNews, User, Log
from ngnotifier.notifs import send_email
from ngnotifier.utils import serializable_object, post_article


@never_cache
def hosts(request):
    if request.POST:
        form = CaptchaForm(request.POST)
        if form.is_valid():
            user, token = form.save()
            context = {
                'user': user,
                'token': token,
                'site_url': settings.SITE_URL
            }
            html_content = render_to_string(
                'email/token.html',
                context,
                context_instance=RequestContext(request)
            )
            if send_email(html_content, 'NG Notifier',
                          settings.FROM_ADDR, user.email, 'html'):
                logout(request)
                return render_to_response(
                    'sent_email.html',
                    context,
                    context_instance=RequestContext(request)
                )
        return render_to_response(
            'fail_subscribe_form.html',
            context_instance=RequestContext(request)
        )
    form = CaptchaForm()
    hosts = NGHost.objects.all()
    context = {
        'form': form,
        'hosts': hosts,
    }
    return render_to_response(
        'hosts.html',
        context,
        context_instance=RequestContext(request)
    )


@never_cache
def group2(request, id):
    group = get_object_or_404(NGGroup, id=id)
    news = NGNews.objects\
        .filter(groups__in=[group.id], father='').order_by('-date').all()

    data = [serializable_object(n) for n in news]
    return JsonResponse(data, safe=False)


@never_cache
def group(request, id):
    news = get_object_or_404(NGGroup, id=id).get_news()
    data = {key.id: key.date.strftime('<b>%Y-%m-%d %H:%M:%S</b> | ')
                    + key.subject for key in news}
    return JsonResponse(data, safe=False)


@never_cache
def news2(request, id):
    news = get_object_or_404(NGNews, id=id)
    data = serializable_object(news, True)
    return JsonResponse(data, safe=False)


@never_cache
def news(request, id):
    news = get_object_or_404(NGNews, id=id)
    data = {
        'from': news.email_from,
        'subject': news.subject,
        'contents': news.contents,
        'date': news.date.strftime('%Y-%m-%d %H:%M:%S'),
        'message-id': news.message_id,
        'lines': news.lines,
        'xref': news.xref,
        'references': news.references,
        'bytes': news.bytes,
        'posted-in': ', '.join([n.name for n in news.groups.all()])
    }
    return JsonResponse(data, safe=False)


def token_validation(request, id, token):
    if request.method != 'GET':
        return hosts(request)
    user = get_object_or_404(User, id=id)
    if user.token == token:
        user.is_active = True
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        auth_login(request, user)
        return edit_settings(request)
    raise Http404()


def unsubscribe(request, id, token):
    if request.method != 'GET':
        return hosts(request)
    user = get_object_or_404(User, id=id)
    if not user.is_active:
        return hosts(request)
    for ng_group in NGGroup.objects.all():
        if user in ng_group.followers:
            ng_group.followers.remove(user)
    auth_login(request, user)
    return render_to_response(
        'unsubscribe_confirmation.html',
        context_instance=RequestContext(request)
    )


def help(request):
    form = CaptchaForm()
    context = {
        'form': form
    }
    return render_to_response(
        'help.html',
        context,
        context_instance=RequestContext(request)
    )


@login_required
def group_follow(request, id):
    ng_group = get_object_or_404(NGGroup, id=id)
    if not request.user in ng_group.followers.all():
        ng_group.followers.add(request.user)
        return JsonResponse({"response": True})
    else:
        raise Http404()


@login_required
def group_unfollow(request, id):
    ng_group = get_object_or_404(NGGroup, id=id)
    if request.user in ng_group.followers.all():
        ng_group.followers.remove(request.user)
        return JsonResponse({"response": True})
    else:
        raise Http404()


@login_required
def edit_settings(request):
    if request.POST:
        form = SettingsForm(request.POST)
        if form.is_valid():
            form.save(request.user)
    return render_to_response(
        'settings.html',
        context_instance=RequestContext(request)
    )


@login_required
def post(request):
    if request.POST:
        groups = request.POST.getlist('groups')
        subject = request.POST.get('subject')
        name = request.POST.get('name')
        email = request.POST.get('email')
        contents = request.POST.get('contents')

        groups = [NGGroup.objects.get(id=id) for id in groups]

        if post_article(name, email, groups, subject, contents):
            post_log = Log()
            post_log.type = 'P'
            post_log.date = datetime.now()
            post_log.user = request.user
            post_log.description = subject + ' ' + name
            post_log.save()
            return render_to_response(
                'news_posted.html',
                context_instance=RequestContext(request)
            )
    hosts = NGHost.objects.all()
    context = {
        'hosts': hosts,
        }
    return render_to_response(
        'post.html',
        context,
        context_instance=RequestContext(request)
    )


def login_user(request):
    logout(request)
    if request.POST:
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Session will expires in 30 days
                request.session.set_expiry(2592000)
                return HttpResponseRedirect(
                    reverse('ngnotifier.views.edit_settings'))
    return render_to_response(
        'fail_login_form.html',
        context_instance=RequestContext(request)
    )


# API
class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)


@api_view(('GET',))
def api_root(request, format=None):
    return Response({
        'hosts': rf_reverse('host_list', request=request, format=format),
        # 'groups': rf_reverse('group-list', request=request, format=format)
    })