# from django.db import models
# Create your models here.
# -*- coding:utf-8 -*-
from django.template.loader import render_to_string


INDICE_BOVESPA = "INDICE:BOVESPA"

VERDE_ALTO  = "#61BF1F"
VERDE_MEDIO = "#468315"
VERDE_BAIXO = "#30560E"

VERMELHOR_ALTO  = "#DE2516"
VERMELHOR_MEDIO = "#93190F"
VERMELHOR_BAIXO = "#550E09"

NEUTRO = "#2A2A2A"

FONTE_CODIGO_ALTA   = "#FFFFFF"
FONTE_VARIACAO_ALTA = "#B0D984"

FONTE_CODIGO_NEUTRO   = "#333333"
FONTE_VARIACAO_NEUTRO = "#333333"

FONTE_CODIGO_VERMELHO_BAIXO   = "#672920"
FONTE_VARIACAO_VERMELHO_BAIXO = "#672920"

FONTE_CODIGO_VERMELHO_MEDIO   = "#A24435"
FONTE_VARIACAO_VERMELHO_MEDIO = "#A24435"

FONTE_CODIGO_VERMELHO_ALTA   = "#FFFFFF"
FONTE_VARIACAO_VERMELHO_ALTA = "#DE8A84"


class Papel(object):

    def __init__(self, codigo):
        from paineldabolsa.views import get_redis
        self.REDIS_SERVER = get_redis()
        self.codigo = codigo
        self.variacao = None

    def get_nome(self):
        codigo = self.codigo
        codigo = ''.join([i for i in codigo if not i.isdigit()])
        return codigo

    def get_preco(self):
        try:
            chave = "%s:D:C" % self.codigo
            key = self.REDIS_SERVER.zrange(chave, -1, -1)
            preco = self.REDIS_SERVER.get(key[0])
            return preco
        except:
            return "N/S"

    def get_variacao(self):
        try:
            if self.variacao == None:
                chave = "%s:D:F" % self.codigo
                key = self.REDIS_SERVER.zrange(chave, -1, -1)
                variacao = self.REDIS_SERVER.get(key[0])
                self.variacao = variacao
            return self.variacao
        except:
            return 0

    def get_mini_painel(self):
        info = self.get_info()
        info['codigo'] = self.codigo
        info['variacao'] = self.get_variacao()

        return render_to_string('paineldabolsa/mini-painel.html', info)

    def get_info(self):
        info = {}
        variacao = float(self.get_variacao())

        if variacao >= 3.0:
            info['background_color']   = VERDE_ALTO
            info['fonte_codigo_cor']   = FONTE_CODIGO_ALTA
            info['fonte_variacao_cor'] = FONTE_VARIACAO_ALTA
        elif variacao >= 2.0:
            info['background_color']   = VERDE_MEDIO
            info['fonte_codigo_cor']   = FONTE_CODIGO_ALTA
            info['fonte_variacao_cor'] = FONTE_VARIACAO_ALTA
        elif variacao >= 1.0:
            info['background_color']   = VERDE_BAIXO
            info['fonte_codigo_cor']   = FONTE_CODIGO_ALTA
            info['fonte_variacao_cor'] = FONTE_VARIACAO_ALTA
        elif variacao >= -1.0:
            info['background_color']   = NEUTRO
            info['fonte_codigo_cor']   = FONTE_CODIGO_NEUTRO
            info['fonte_variacao_cor'] = FONTE_VARIACAO_NEUTRO
        elif variacao >= -2.0:
            info['background_color']   = VERMELHOR_BAIXO
            info['fonte_codigo_cor']   = FONTE_CODIGO_VERMELHO_BAIXO
            info['fonte_variacao_cor'] = FONTE_VARIACAO_VERMELHO_BAIXO
        elif variacao >= -3.0:
            info['background_color']   = VERMELHOR_MEDIO
            info['fonte_codigo_cor']   = FONTE_CODIGO_VERMELHO_MEDIO
            info['fonte_variacao_cor'] = FONTE_VARIACAO_VERMELHO_MEDIO
        else:
            info['background_color']   = VERMELHOR_ALTO
            info['fonte_codigo_cor']   = FONTE_CODIGO_VERMELHO_ALTA
            info['fonte_variacao_cor'] = FONTE_VARIACAO_VERMELHO_ALTA

        return info


