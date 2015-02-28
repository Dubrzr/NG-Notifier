from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.views import login
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.template.loader import render_to_string
from ngnotifier import settings
from ngnotifier.forms import CaptchaForm, SettingsForm
from ngnotifier.models import NGHost, NGGroup, NGNews, User
from ngnotifier.notifs import send_email
from django.contrib.auth import logout
from ngnotifier.utils import serializable_object


def hosts(request):
    if request.user.is_authenticated():
        request.session.set_expiry(2592000) # Session will expires in 30 days
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
            if send_email(html_content, 'NL Notifier',
                          settings.FROM_ADDR, user.email, 'html'):
                logout(request)
                return render_to_response(
                    'sent_email.html',
                    context,
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


def group2(request, id):
    group = get_object_or_404(NGGroup, id=id)
    news = NGNews.objects\
        .filter(groups__in=[group.id], father='').order_by('-date').all()

    data = [serializable_object(n) for n in news]
    return JsonResponse(data, safe=False)


def group(request, id):
    news = get_object_or_404(NGGroup, id=id).get_news()
    data = {key.id: key.date.strftime('<b>%Y-%m-%d %H:%M:%S</b> | ')
                    + key.subject for key in news}
    return JsonResponse(data, safe=False)


def news2(request, id):
    news = get_object_or_404(NGNews, id=id)
    data = serializable_object(news, True)
    return JsonResponse(data, safe=False)


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
            print('saved')
    return render_to_response(
        'settings.html',
        context_instance=RequestContext(request)
    )


def login_user(request):
    logout(request)
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = User.objects.get(email=username)
        print(user.check_password(password))

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/settings')
    raise Http404()
