from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.auth.views import logout

from ngnotifier.settings import SITE_URL, SITE_URL_PREFIX
from ngnotifier import api_views


admin.autodiscover()

api_urlpatterns = patterns(
    '',
    url(r'^$', api_views.host_list, name='host_list'),
    url(r'^topic/(?P<news_id>.+)/$', api_views.news_detail,
        name='news_detail'),
    url(r'^(?P<host>.+)/(?P<group>.+)/search$', api_views.search,
        name='search_group'),
    url(r'^(?P<host>.+)/search$', api_views.search, name='search_host'),
    url(r'^search$', api_views.search, name='search'),
    url(r'^(?P<host>.+)/(?P<group>.+)/refresh/$', api_views.news_list_refresh,
        name='news_list_refresh'),
    url(r'^(?P<host>.+)/(?P<group>.+)/$', api_views.news_list,
        name='news_list'),
    url(r'^(?P<host>.+)/$', api_views.group_list, name='group_list'),
)

base_urlpatterns = patterns(
    '',
    url(r'^$', 'ngnotifier.views.hosts', name='home'),
    url(r'^group/(?P<id>[0-9A-Za-z]+)/$', 'ngnotifier.views.group',
        name='group'),
    url(r'^group2/(?P<id>[0-9A-Za-z]+)/$', 'ngnotifier.views.group2',
        name='group2'),
    url(r'^group/follow/(?P<id>[0-9]+)/$', 'ngnotifier.views.group_follow',
        name='group_follow'),
    url(r'^group/unfollow/(?P<id>[0-9]+)/$', 'ngnotifier.views.group_unfollow',
        name='group_unfollow'),
    url(r'^post/$', 'ngnotifier.views.post', name='post'),
    url(r'^news/(?P<id>[0-9A-Za-z]+)/$', 'ngnotifier.views.news', name='news'),
    url(r'^news2/(?P<id>[0-9A-Za-z]+)/$', 'ngnotifier.views.news2',
        name='news2'),
    url(r'^settings/$', 'ngnotifier.views.edit_settings', name='edit_settings'),
    url(r'^help$', 'ngnotifier.views.help', name='help'),
    url(r'^unsubscribe/(?P<id>[0-9]+)-(?P<token>.+)/$',
        'ngnotifier.views.unsubscribe', name='unsubscribe'),
    url(r'^(?P<id>[0-9]+)-(?P<token>.+)$', 'ngnotifier.views.token_validation',
        name='token_validation'),
    url(r'^accounts/login/$', 'ngnotifier.views.login_user', name='login'),
    url(r'^accounts/logout/$', logout, {'next_page': SITE_URL}, name='logout'),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^api/', include(api_urlpatterns))
)

urlpatterns = patterns(
    '',
    url(r'^' + SITE_URL_PREFIX, include(base_urlpatterns))
)
