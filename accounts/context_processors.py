from .models import SiteSetting

def site_settings(request):
    return {
        "setting": SiteSetting.objects.first()
    }
