# -*- coding:utf-8 -*-
from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def revision():
    revision = settings.BASE_DIR.ancestor(1).child('REVISION')
    if revision.exists():
        return revision.read_file()
    else:
        return u"Não Informada"
