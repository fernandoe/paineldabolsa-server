# -*- coding:utf-8 -*-
import logging

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http.request import HttpRequest
from django.shortcuts import redirect
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
import requests
from django.views.decorators.http import require_http_methods
import redis

from paineldabolsa.business import BovespaServiceRedis
from paineldabolsa.models import Papel
from django.http.response import HttpResponse


# from django.shortcuts import render
# Create your views here.
logger = logging.getLogger(__name__)

INDICES = [
    'IBOVESPA',
    'ICON',
    'IEE',
    'IFNC',
    'IMAT',
    'IMOB',
    'INDX',
    'UTIL',
]


def get_redis():
    REDIS_SERVER = getattr(settings, "REDIS_SERVER", None)
    if REDIS_SERVER == None:
        address = getattr(settings, 'REDIS_SERVER_ADDRESS', '127.0.0.1')
        REDIS_SERVER = redis.StrictRedis(host=address, port=6379, db=0)
        settings.REDIS_SERVER = REDIS_SERVER
    return REDIS_SERVER


@require_http_methods(["GET"])
def paineldabolsa(request):
    rc = RequestContext(request)

    service = BovespaServiceRedis()
    dados = dict((indice,[]) for indice in INDICES)
    for indice in INDICES:
        papeis = service.papeis_do_indice(indice)
        for codigo in papeis:
            dados[indice].append(Papel(codigo))
    rc.update(dados)

    r = get_redis()
    rc["DATA"] = r.get(settings.REDIS_DATA)
    rc["HORA"] = r.get(settings.REDIS_HORA)

    return render_to_response('paineldabolsa/index.html', rc)


@require_http_methods(["GET"])
def grafico(request, papel_codigo):
    link = "http://chart.finance.yahoo.com/z?s=%s.sa&q=c&p=m10,m30,v&lang=pt-BR" % papel_codigo
    r = requests.get(link)

    response = HttpResponse(content_type='image/png')
    response.write(r.content)
    return response


@require_http_methods(["GET"])
def paineldabolsa_ibovespa(request):
    rc = RequestContext(request)

    service = BovespaServiceRedis()
    dados = dict((indice,[]) for indice in INDICES)
    for indice in INDICES:
        papeis = service.papeis_do_indice(indice)
        for codigo in papeis:
            dados[indice].append(Papel(codigo))
    rc.update(dados)

    r = get_redis()
    rc["DATA"] = r.get(settings.REDIS_DATA)
    rc["HORA"] = r.get(settings.REDIS_HORA)

    return render_to_response('paineldabolsa/ibovespa.html', rc)

