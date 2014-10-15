from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'paineldabolsa.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    (r'^$', RedirectView.as_view(url="/paineldabolsa/")),


    url(r'^admin/', include(admin.site.urls)),
    (r'^paineldabolsa/'      , include('paineldabolsa.urls')),
)
