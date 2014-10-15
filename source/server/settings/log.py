# -*- coding:utf-8 -*-
# import os

"""
DEBUG    : Low level system information for debugging purposes.
INFO     : General system information.
WARNING  : Information describing a minor problem that has occurred.
ERROR    : Information describing a major problem that has occurred.
CRITICAL : Information describing a critical problem that has occurred.
"""
LOG_NIVEL = 'DEBUG'# 'DEBUG' if settings.DEBUG else 'INFO'

#  = Path(__file__).ancestor(3)
from server.settings.base import BASE_DIR
BASE_LOG_FOLDER = BASE_DIR.ancestor(1).child('log')
FILE_LOG_SERVER = BASE_LOG_FOLDER.child('server.log')

# FILE_LOG_PUSH = os.path.join(BASE_LOG_FOLDER, 'push.log')
# FILE_LOG_REDIS_YAHOO = os.path.join(BASE_LOG_FOLDER, 'redis_yahoo.log')
# from logging import Formatter
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s | %(thread)d | %(levelname)s | %(module)s | %(filename)s(%(lineno)d) | %(message)s'
#             'format': '%(asctime)s | %(thread)d | %(levelname)s | %(module)s | %(pathname)s%(filename)s(%(lineno)d) | %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level'        : 'ERROR',
            'class'        : 'django.utils.log.AdminEmailHandler',
            'include_html' : True,
        },
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level'     : 'DEBUG',
            'class'     : 'logging.StreamHandler',
            'formatter' : 'verbose'
        },
        'file_handler':{
            'level'     : 'DEBUG',
            'class'     : 'logging.handlers.TimedRotatingFileHandler',
            'formatter' : 'verbose',
            'filename'  : FILE_LOG_SERVER,
            'when'      : 'midnight',
        },
    },
    'loggers': {
        'django': {
            'handlers'  : ['null'],
            'propagate' : True,
            'level'     :'INFO',
        },
        '': {
            'handlers': [ 'console', 'file_handler' ],
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers'  : ['mail_admins'],
            'level'     : 'ERROR',
            'propagate' : True,
        },
    }
}
