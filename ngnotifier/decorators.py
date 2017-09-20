from django.http import HttpResponse
from ngnotifier.models import DeviceSession
from ngnotifier.settings import API_KEY


def api_key_required(func):
    def decorator(request, *args, **kwargs):
        if API_KEY == '':
            return HttpResponse(status=500)
        api_key = request.META.get('HTTP_KEY', '')
        if api_key != API_KEY:
            return HttpResponse(status=403)
        return func(request, *args, **kwargs)
    return decorator

def device_login_required(func):
    def decorator(request, *args, **kwargs):
        session_key = request.META.get('HTTP_SESSION', '')
        try:
            device_session = DeviceSession.objects.get(session_key=session_key)
        except:
            return HttpResponse(status=403)
        kwargs.update({'device_session': device_session})
        return func(request, *args, **kwargs)
    return decorator
