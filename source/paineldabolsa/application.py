from flask import Flask, render_template
import redis

from business import BovespaServiceRedis
from models import Papel


app = Flask(__name__)
app.config.from_object('source.settings.development')
app.config.from_envvar('PRODUCTION_SETTINGS', silent=True)


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
    REDIS_SERVER = app.config.get("REDIS_SERVER", None)
    if REDIS_SERVER == None:
        address = app.config.get("REDIS_SERVER_ADDRESS")
        REDIS_SERVER = redis.StrictRedis(host=address, port=6379, db=0)
        app.config['REDIS_SERVER'] = REDIS_SERVER
    return REDIS_SERVER


@app.route("/")
def hello():
    service = BovespaServiceRedis()

    dados = dict((indice,[]) for indice in INDICES)
    for indice in INDICES:
        papeis = service.papeis_do_indice(indice)
        for codigo in papeis:
            dados[indice].append(Papel(codigo))

    return render_template(
            'index2.html', 
            revision = app.config.get("REVISION"),
            debug    = app.config.get("DEBUG"),
            **dados
        )

if __name__ == "__main__":
    app.run()


