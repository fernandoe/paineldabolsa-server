# -*- coding:utf-8 -*-
from .base import *

REDIS_SERVER_ADDRESS = '127.0.0.1'

#===================================================================================================
# ===============[ DJANGO ]===============
#===================================================================================================
DEBUG = False
DEBUG_PROPAGATE_EXCEPTIONS = False
TEMPLATE_DEBUG = False
STATIC_ROOT = "/home/ubuntu/paineldabolsa-server-static"
ALLOWED_HOSTS = [
    'paineldabolsa.com.br',
    'www.paineldabolsa.com.br',
    '107.170.42.230'
]

#===================================================================================================
# ===============[ PAINEL DA BOLSA ]===============
#===================================================================================================
def file_get_contents(filename):
    with open(filename) as f:
        return f.read()

REVISION = file_get_contents("/home/ubuntu/paineldabolsa-server/current/REVISION")
