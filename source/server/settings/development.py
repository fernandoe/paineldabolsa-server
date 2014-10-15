# -*- coding:utf-8 -*-
import os
from .base import *

REDIS_SERVER_ADDRESS = '127.0.0.1'
REDIS_SERVER = None

PROXIES = {
    'http'  : os.environ['http_proxy'],
    'https' : os.environ['https_proxy'],
}

# REVISION = u"NÃO INFORMADO"

#===================================================================================================
# ===============[ DJANGO ]===============
#===================================================================================================
DEBUG = True
DEBUG_PROPAGATE_EXCEPTIONS = True
TEMPLATE_DEBUG = True
INTERNAL_IPS = ('127.0.0.1',)
