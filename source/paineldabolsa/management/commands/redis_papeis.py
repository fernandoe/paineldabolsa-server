# -*- coding:utf-8 -*-
import datetime
import logging

from django.conf import settings
from django.core.management.base import BaseCommand

from paineldabolsa.views import get_redis


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        inicio = datetime.datetime.now()
        redis = get_redis()
        redis.delete(settings.REDIS_PAPEIS)
        for indice in settings.REDIS_INDICES:
            redis.delete(settings.REDIS_INDICE % indice)
            f = open('../sandbox/indices/%s.txt' % indice)
            papeis = [line.strip() for line in f]
            f.close()
            for papel in papeis:
                codigo = papel
                redis.sadd(settings.REDIS_PAPEIS, codigo)
                redis.sadd(settings.REDIS_INDICE % indice, codigo)
        logger.info(u"Adicionado '%s' papéis" % len(papeis))
        logger.info(u'Processo finalizado: %s' % (datetime.datetime.now() - inicio))


