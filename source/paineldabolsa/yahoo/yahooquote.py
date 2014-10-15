# -*- coding:utf-8 -*-
import datetime
from decimal import Decimal
import logging
import urllib

from django.conf import settings


logger = logging.getLogger(__name__)


def __request(symbol, stat):
    #http://finance.yahoo.com/d/quotes.csv?f=sd1t1oghl1v&s=PETR4.SA
    url = 'http://finance.yahoo.com/d/quotes.csv?s=%s.SA&f=%s' % (symbol, stat)
    return urllib.urlopen(url, proxies=settings.PROXIES).read().strip().strip('"')


def get_daily_information(symbol):
    # s - Symbol
    # sd1 - Last Trade Date
    # t1 - Last Trade Time
    # o - Open
    # g - Day's Low
    # h - Day's High
    # l1 - Last Trade (Price Only)
    # v - Volume
    # p2 - Variação
    values = None
    try:
        values = __request(symbol, 'sd1t1oghl1vp2').split(',')

#         import ipdb
#         ipdb.set_trace()

        data = {}
        data['symbol'] = values[0]
        data['data'] = values[1]
        data['hora'] = values[2]
        data['abertura'] = values[3]
        data['minima'] = values[4]
        data['maxima'] = values[5]
        data['ultimo'] = values[6]
        data['volume'] = values[7]

        variacao = values[8]
        data['variacao'] = variacao.replace('"', '').replace('%', '')
        return data
    except Exception, e:
        logger.error('Erro pegando cotações do yahoo: %s' % (e))
        logger.error(str(values))
        logger.exception(e)



def _convert_hour(hora):
    result = datetime.datetime.strptime(hora, '"%I:%M%p"')
    return (result + datetime.timedelta(minutes=180))


def _convert_date(date):
    if date == '"N/A"':
        return None
    result = datetime.datetime.strptime(date, '"%m/%d/%Y"')
    return result


def _convert_variacao(variacao):
    try:
        return Decimal(variacao[1:len(variacao)-2])
    except Exception, e:
        logger.error('Erro tentando converter valor: ' % variacao)
        logger.exception(e)


