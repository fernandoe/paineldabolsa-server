# -*- coding:utf-8 -*-
import datetime
from decimal import Decimal
import logging
import threading

from yahooquote import get_daily_information


logger = logging.getLogger(__name__)


class RedisYahooWorker(threading.Thread):

    def __init__(self, queue, nome):
        self.__nome = nome
        self.__queue = queue
        threading.Thread.__init__(self)

    def run(self):
        logger.debug("%s - Iniciando worker..." % (threading.currentThread().name))

        while True:
            item = self.__queue.get()
            if item is None:
                logger.info("%s - Finalizando worker..." % (threading.currentThread().name))
                break
            logger.info("Processando %s com a thread %s" % (item, threading.currentThread().name))
            try:
                update_redis(item)
            except Exception, e:
                logger.exception(e)

            self.__queue.task_done()


def update_redis(papel_codigo):
    from paineldabolsa.views import get_redis
    r = get_redis()
    info = get_daily_information(papel_codigo)
    if info is None:
        return
    try: 
        data =  _convert_date(info['data'])
    except Exception, e:
        logger.info('ERRO CONVERTENDO DATA: Papel (%s) - Mensagem: %s - info: %s' % (papel_codigo, e, info))
        return
    if data is None:
        logger.info('Papel "%s" nao tem informacoes necessarias para ser incluido!' % papel_codigo)
        return


    # Dados diários
    key_o = '%s:D:%s:O' % (papel_codigo, data.strftime('%Y%m%d'))
    key_c = '%s:D:%s:C' % (papel_codigo, data.strftime('%Y%m%d'))
    key_h = '%s:D:%s:H' % (papel_codigo, data.strftime('%Y%m%d'))
    key_l = '%s:D:%s:L' % (papel_codigo, data.strftime('%Y%m%d'))
    key_v = '%s:D:%s:V' % (papel_codigo, data.strftime('%Y%m%d'))
    key_f = '%s:D:%s:F' % (papel_codigo, data.strftime('%Y%m%d')) #fluctuation

    r.set(key_o, info['abertura'])
    r.set(key_c, info['ultimo'])
    r.set(key_h, info['maxima'])
    r.set(key_l, info['minima'])
    r.set(key_v, info['volume'])
    r.set(key_f, info['variacao'])
    r.zadd("%s:D:O" % papel_codigo, data.strftime('%Y%m%d'), key_o)
    r.zadd("%s:D:C" % papel_codigo, data.strftime('%Y%m%d'), key_c)
    r.zadd("%s:D:H" % papel_codigo, data.strftime('%Y%m%d'), key_h)
    r.zadd("%s:D:L" % papel_codigo, data.strftime('%Y%m%d'), key_l)
    r.zadd("%s:D:V" % papel_codigo, data.strftime('%Y%m%d'), key_v)
    r.zadd("%s:D:F" % papel_codigo, data.strftime('%Y%m%d'), key_f)

    logger.info('O papel "%s" foi adicionado com sucesso' % papel_codigo)


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
        logger.info('Erro tentando converter valor: %s' % variacao)
        logger.exception(e)



