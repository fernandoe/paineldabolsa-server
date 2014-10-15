# -*- coding:utf-8 -*-
import Queue
import datetime
import logging
import time

from django.core.management.base import BaseCommand

from paineldabolsa.business import BovespaServiceRedis
from paineldabolsa.views import get_redis
from paineldabolsa.yahoo.yahoo import RedisYahooWorker
from django.conf import settings


logger = logging.getLogger(__name__)


WORKERS = 30


class Command(BaseCommand):
    def handle(self, *args, **options):
        inicio = datetime.datetime.now()

        queue = Queue.Queue()
        service = BovespaServiceRedis()
        papeis = service.papeis()

        for _papel in papeis:
            logger.info("Colocando na fila: %s" % _papel)
            queue.put(_papel)

        logger.info("Fila pronta com '%s' elemento(s)." % len(papeis))

        for i in range(WORKERS):
            t = RedisYahooWorker(queue, ("(%s)"%i))
            t.setDaemon(False)
            t.start()

        queue.join()

        for i in range(WORKERS):
            queue.put(None)

        r = get_redis()

        data = time.strftime("%d/%m/%Y")
        hora = time.strftime("%H:%M")
 
        r.set(settings.REDIS_DATA, data)
        r.set(settings.REDIS_HORA, hora)

        logger.info(u'Processo finalizado: %s' % (datetime.datetime.now() - inicio))


