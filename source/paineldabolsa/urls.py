# -*- coding:utf-8 -*-
from django.conf.urls import patterns, url


urlpatterns = patterns('paineldabolsa.views',
    url(r'^$', 'paineldabolsa', name="paineldabolsa"),
    url(r'^grafico/(?P<papel_codigo>.{0,10})/$', 'grafico', name="grafico"),

    url(r'^ibovespa/$', 'paineldabolsa_ibovespa', name="paineldabolsa_ibovespa"),
)


