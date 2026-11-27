import os

from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import re_path

from project.main import common, page, plant, user, template, controller, \
    mmanager, timeplot, alarm, report
from settings import deploy

admin.autodiscover()


urlpatterns = [
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    re_path(r'^admin/', admin.site.urls),

    re_path(r'^$', common.frontpage),
    re_path(r'^p/(.*)/(?P<id>\d+)/$', page.show),

    re_path(r'^page/list/$', page.list_pages),
    re_path(r'^page/edit/(?P<plant_id>\d+)/$', page.edit),
    re_path(r'^page/edit/(?P<plant_id>\d+)/(?P<id>\d+)/$', page.edit),
    re_path(r'^page/delete/(?P<plant_id>\d+)/(?P<id>\d+)/$', page.delete),
    re_path(r'^page/delete/(?P<id>\d+)/$', page.delete),
    re_path(r'^page/edit/get_order_area/(?P<parent_page>\d+)/(?P<current_page>\d+)/$', page.get_order_area),
    re_path(r'^page/toggle_public/(?P<plant_id>\d+)/(?P<id>\d+)/$', page.toggle_public),
    re_path(r'^page/toggle_public/(?P<id>\d+)/$', page.toggle_public),
    re_path(r'^page/toggle_published/(?P<plant_id>\d+)/(?P<id>\d+)/$', page.toggle_published),
    re_path(r'^page/toggle_published/(?P<id>\d+)/$', page.toggle_published),
    re_path(r'^page/site_list/$', page.site_list),
    re_path(r'^plant/list/$', plant.list_plants),
    re_path(r'^plant/edit/$', plant.edit),
    re_path(r'^plant/edit/(?P<id>\d+)/$', plant.edit),
    re_path(r'^plant/change_order/(?P<direction>\w+)/(?P<id>\d+)/$', plant.change_order),
    re_path(r'^plant/delete/(?P<id>\d+)/$', plant.delete),
    re_path(r'^plant/toggle_public/(?P<id>\d+)/$', plant.toggle_public),
    re_path(r'^plant/page_list/(?P<id>\d+)/$', page.plant_page_list),

    re_path(r'^user/list/$', user.list_users),
    re_path(r'^user/edit/$', user.edit),
    re_path(r'^user/edit/(?P<id>\d+)/$', user.edit),
    re_path(r'^user/delete/(?P<id>\d+)/$', user.delete),
    re_path(r'^user/toggle_active/(?P<id>\d+)/$', user.toggle_active),
    re_path(r'^user/related/$', user.related),
    re_path(r'^profile/edit/$', user.edit_profile),

    re_path(r'^template/list/$', template.list_templates),
    re_path(r'^template/edit/$', template.edit),
    re_path(r'^template/edit/(?P<id>\d+)/$', template.edit),
    re_path(r'^template/delete/(?P<id>\d+)/$', template.delete),
    re_path(r'^template/toggle_published/(?P<id>\d+)/$', template.toggle_published),
    re_path(r'^template/change_order/(?P<direction>\w+)/(?P<id>\d+)/$', template.change_order),

    re_path(r'^controller/list/$', controller.list_controllers),
    re_path(r'^controller/edit/$', controller.edit),
    re_path(r'^controller/edit/(?P<id>\d+)/$', controller.edit),
    re_path(r'^controller/delete/(?P<id>\d+)/$', controller.delete),
    re_path(r'^controller/toggle_active/(?P<id>\d+)/$', controller.toggle_active),

    re_path(r'^mmanager/list/$', mmanager.list_media),
    re_path(r'^mmanager/select_image/(?P<plant_id>\d+)/$', mmanager.select_image),

    re_path(r'^accounts/login/$', user.login),
    re_path(r'^signout/$', user.signout),

    re_path(r'^service/check_username_password/$', user.check_username_password),
    re_path(r'^service/username_exists/(?P<username>.*)/$', user.username_exists),
    re_path(r'^service/valid_email/(?P<email>(.*))/$', user.valid_email),
    re_path(r'^scgi/$', common.create_comm_request),
    re_path(r'^service/get_timeplot_data/(?P<params>.*)/$', timeplot.get_timeplot_data),
    re_path(r'^service/download_timeplot_data/(?P<params>.*)/$', timeplot.download_timeplot_data),
    re_path(r'^service/alarms/get/(?P<plant_id>\d+)/(?P<nad>\w+)/(?P<filter_type>\w+)/(?P<filter_activity>\w+)/(?P<items_per_page>\d+)/(?P<page_index>\d+)/(?P<rw_access>\d+)/(?P<download_btn>\d+)/$', alarm.get_alarms),
    re_path(r'^service/alarms/download/(?P<plant_id>\d+)/(?P<nad>\w+)/(?P<filter_type>\w+)/(?P<filter_activity>\w+)/(?P<items_per_page>\d+)/(?P<page_index>\d+)/$', alarm.download_alarms),
    re_path(r'^service/alarms/ack/(?P<id>\d+)/$', alarm.ack_alarm),
    re_path(r'^service/get_available_user_list/$', user.get_available_user_list),
    re_path(r'^service/get_user_list_row/(?P<id>\d+)/$', user.get_user_list_row),
    re_path(r'^service/get_available_controller_list/$', controller.get_available_controller_list),
    re_path(r'^service/get_controller_list_row/(?P<id>\d+)/$', controller.get_controller_list_row),
    re_path(r'^service/nad_valid/(?P<nad>.*)/$', controller.nad_valid),

    re_path(r'^timeplot/(?P<timeplot_id>.*)/(?P<graphstyle>.*)/(?P<tags>.*)/(?P<min>.*)/(?P<max>.*)/(?P<colors>.*)/(?P<decimals>.*)/(?P<legend_labels>.*)/(?P<legend_unit>.*)/(?P<show_legend>.*)/(?P<page>.*)/$', timeplot.show_fullscreen),

    re_path(r'^test_report/$', report.test_alarms_report),

    # fix for highslide hardcoded links
    re_path(r'^p/.*/\d+(?P<image>/highslide/graphics/.*)$', page.redirect_highslide_statics),
]

if not deploy.WEB_DEPLOY:
    urlpatterns += \
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + \
        static('/data/', document_root=os.path.join(
            settings.PROJECT_PATH, '..', 'data/'
        ))
    urlpatterns += debug_toolbar_urls()
