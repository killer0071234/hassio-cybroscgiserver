from django.conf import settings

from project.main.models import get_default_page as model_get_default_page


def get_default_page(request):
    return {
        'get_default_page': model_get_default_page(),
    }


def get_site_name(request):
    return {
        'get_site_name': settings.STATIC_SETTINGS["site_name"],
    }


def get_contact_email(request):
    return {
        'get_contact_email':
            settings.STATIC_SETTINGS["contact_email"],
    }


def get_head_caption(request):
    return {
        'get_head_caption': settings.STATIC_SETTINGS["head_caption"],
    }


def get_footer_text(request):
    return {
        'get_footer_text': settings.STATIC_SETTINGS["footer_text"],
    }


def get_google_webmaster_tools_code(request):
    return {
        'get_google_webmaster_tools_code':
            settings.STATIC_SETTINGS["google_webmaster_tools_code"],
    }


def get_shortcut_icon(request):
    return {
        'get_shortcut_icon':
            settings.STATIC_SETTINGS["shortcut_icon"],
    }
