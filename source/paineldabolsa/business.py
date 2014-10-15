# -*- coding:utf-8 -*-
import datetime
from decimal import Decimal
import logging



logger = logging.getLogger(__name__)

# PAPEIS = 'PAPEIS'
# PAPEIS_CACHE = 'PAPEIS:CACHE'
INDICE = "INDICE:%s"
PAPEIS = "PAPEIS"
TTL = 1*60*60*24*3 # 3 dias

class BovespaServiceRedis(object):

    def __init__(self):
        from paineldabolsa.views import get_redis
        self.r = get_redis()


    def papeis(self):
        return self.r.smembers(PAPEIS)


    def papeis_do_indice(self, indice):
        return self.r.smembers(INDICE % indice)


    def papel_existe(self, papel_codigo):
        from bovespa.models import Papel
        """
        Retorna True se o papel existe ou False em caso contrário
        1. Verifica na lista de papéis ativos na bolsa
        2. Verifica na lista de papéis em cache (não estão ativos na bolsa de valores)
        3. Verifica na tabela com todos os papéis da bolsa de valores
        """
        if self.r.sismember(PAPEIS, papel_codigo) or self.r.sismember(PAPEIS_CACHE, papel_codigo):
            return True
        else:
            if Papel.objects.filter(codigo=papel_codigo).count() > 0:
                self.historico_to_redis_diario(papel_codigo, TTL)
                self.historico_to_redis_semanal(papel_codigo, TTL)
                self.historico_to_redis_mensal(papel_codigo, TTL)
                self.r.sadd(PAPEIS_CACHE, papel_codigo)
                return True
            else: # Papel não existe retornar False
                return False

    def numero_de_periodos(self, papel_codigo, periodo='D'):
        """
        Retorna o número de períodos que um papel tem em cache ou na base de dados.
        """
        zkey = '%s:%s:C' % (papel_codigo, periodo)
        if self.r.sismember(PAPEIS, papel_codigo):
            total = self.r.zcard(zkey)
            if total > 300:
                total = 300
        elif self.r.sismember(PAPEIS_CACHE, papel_codigo):
            total = self.r.zcard(zkey)
            if total > 300:
                total = 300
        else:
            self.historico_to_redis_diario(papel_codigo, TTL)
            self.historico_to_redis_semanal(papel_codigo, TTL)
            self.historico_to_redis_mensal(papel_codigo, TTL)
            self.r.sadd(PAPEIS_CACHE, papel_codigo)
            total = self.r.zcard(zkey)
            if total > 300:
                total = 300

        logger.debug("numero_de_periodos: %s" % total)
        return total


    def grafico_labels(self, papel_codigo, periodo='D'):
        zkey = '%s:%s:C' % (papel_codigo, periodo)
        labels = []
        if self.r.sismember(PAPEIS, papel_codigo):
            if 'D' == periodo:
                for key, score in self.r.zrange(zkey, -300, -1, withscores=True):
                    ano = str(score)[0:4]
                    mes = str(score)[4:6]
                    dia = str(score)[6:8]
                    data = chartTime(ano, mes, dia)
                    labels.append(data)
            elif 'S' == periodo:
                for key, score in self.r.zrange(zkey, -300, -1, withscores=True):
                    key_semanal = str(int(score)) + '1'
                    data_semana = datetime.datetime.strptime(key_semanal, '%Y%W%w')
#                    print data_semana
                    ano = data_semana.year
                    mes = data_semana.month
                    dia = data_semana.day
                    data = chartTime(ano, mes, dia)
                    labels.append(data)
            elif 'M' == periodo:
                for key, score in self.r.zrange(zkey, -300, -1, withscores=True):
                    ano = str(score)[0:4]
                    mes = str(score)[4:6]
                    data = chartTime(ano, mes)
                    labels.append(data)
        return labels


    def grafico_maximas(self, papel_codigo, periodo='D'):
        zkey = '%s:%s:H' % (papel_codigo, periodo)
        return self.r.mget(self.r.zrange(zkey, -300, -1, withscores=False))


    def grafico_minimas(self, papel_codigo, periodo='D'):
        zkey = '%s:%s:L' % (papel_codigo, periodo)
        return self.r.mget(self.r.zrange(zkey, -300, -1, withscores=False))


    def grafico_aberturas(self, papel_codigo, periodo='D'):
        zkey = '%s:%s:O' % (papel_codigo, periodo)
        return self.r.mget(self.r.zrange(zkey, -300, -1, withscores=False))


    def grafico_fechamentos(self, papel_codigo, periodo='D'):
        zkey = '%s:%s:C' % (papel_codigo, periodo)
        return self.r.mget(self.r.zrange(zkey, -300, -1, withscores=False))


    def grafico_volumes(self, papel_codigo, periodo='D'):
        zkey = '%s:%s:V' % (papel_codigo, periodo)
        return self.r.mget(self.r.zrange(zkey, -300, -1, withscores=False))

    def get_papel_info(self, papel_codigo):

        if (not self.r.sismember(PAPEIS, papel_codigo)) and (not self.r.sismember(PAPEIS_CACHE, papel_codigo)):
            logger.debug(u"Histórico para o papel '%s' ainda não carregado. Carregando...", papel_codigo)
            self.historico_to_redis_diario(papel_codigo, TTL)
            self.historico_to_redis_semanal(papel_codigo, TTL)
            self.historico_to_redis_mensal(papel_codigo, TTL)
            self.r.sadd(PAPEIS_CACHE, papel_codigo)

        variacao = 0.0
        var_keys = self.r.zrange('%s:D:C' % (papel_codigo), -2, -1, withscores=False)
        if len(var_keys) == 2:
            var_valores = self.r.mget(var_keys)
            variacao = ((float(var_valores[1]) / float(var_valores[0]))-1) * 100.0
        else:
            variacao = 0.0

        key = '%s:D:C' % (papel_codigo)
        try:
            ultimo = float(self.r.get(self.r.zrange(key, -1, -1, withscores=False)[0]))
        except Exception, e:
            logger.error("Key: %s" % key)
            logger.exception(e)
            ultimo = None 

        # Pega a data do último candle
        key = '%s:D:O' % (papel_codigo)
        try:
            data_candle = self.r.zrange(key, -1, -1, withscores=True)[0][1]
            data_candle = str(int(data_candle))
            data_candle = "%s/%s/%s" % (data_candle[6:8], data_candle[4:6], data_candle[0:4])
        except Exception, e:
            logger.error("Key: %s" % key)
            logger.exception(e)
            data_candle = None 

        hora = '00:00'

        return data_candle, hora, ultimo, round(variacao, 4)


    def get_papel_detalhe(self, papel_codigo):
        from bovespa.models import Papel

        papel = Papel.objects.get(codigo=papel_codigo)

        variacao = 0.0
        var_keys = self.r.zrange('%s:D:C' % (papel.codigo), -2, -1, withscores=False)
        if len(var_keys) == 2:
            var_valores = self.r.mget(var_keys)
            variacao = ((float(var_valores[1]) / float(var_valores[0]))-1) * 100.0

        # Pega a data do último candle
        data_candle = self.r.zrange('%s:D:O' % (papel_codigo), -1, -1, withscores=True)[0][1]
        data_candle = str(int(data_candle))
        data_candle = "%s/%s/%s" % (data_candle[6:8], data_candle[4:6], data_candle[0:4])

        data = dict()
        data['codigo']          = papel.codigo
        data['nome']            = papel.nome
        data['data']            = data_candle  #'21/12/2012' #candle.data.strftime('%d/%m/%Y')
        data['abertura']        = float(self.r.get(self.r.zrange('%s:D:O' % (papel.codigo), -1, -1, withscores=False)[0]))  #float(candle.abertura)
        data['fechamento']      = float(self.r.get(self.r.zrange('%s:D:C' % (papel.codigo), -1, -1, withscores=False)[0])) #float(candle.fechamento)
        data['minima']          = float(self.r.get(self.r.zrange('%s:D:L' % (papel.codigo), -1, -1, withscores=False)[0])) #float(candle.minima)
        data['maxima']          = float(self.r.get(self.r.zrange('%s:D:H' % (papel.codigo), -1, -1, withscores=False)[0])) #float(candle.maxima)
        data['variacao']        = round(variacao, 4)
        data['grafico_diario']  = '%s%s' % (settings.HOME_ADDRESS, reverse('v1_grafico_financeiro', kwargs={'papel_codigo':papel_codigo, 'periodo':'D' }))
        data['grafico_semanal'] = '%s%s' % (settings.HOME_ADDRESS, reverse('v1_grafico_financeiro', kwargs={'papel_codigo':papel_codigo, 'periodo':'S' }))
        data['grafico_mensal']  = '%s%s' % (settings.HOME_ADDRESS, reverse('v1_grafico_financeiro', kwargs={'papel_codigo':papel_codigo, 'periodo':'M' }))

        return data


    def historico_to_redis(self, historico, periodo, ttl=0):
        r = self.r
        h = historico
        if periodo == 'D':
            papel = h.papel.codigo
            key_o = '%s:D:%s:O' % (papel, date(h.data, 'Ymd'))
            key_c = '%s:D:%s:C' % (papel, date(h.data, 'Ymd'))
            key_h = '%s:D:%s:H' % (papel, date(h.data, 'Ymd'))
            key_l = '%s:D:%s:L' % (papel, date(h.data, 'Ymd'))
            key_v = '%s:D:%s:V' % (papel, date(h.data, 'Ymd'))
            r.set(key_o, h.preabe)
            r.set(key_c, h.preult)
            r.set(key_h, h.premax)
            r.set(key_l, h.premin)
            r.set(key_v, h.voltot)
            r.zadd("%s:D:O" % papel, date(h.data, 'Ymd'), key_o)
            r.zadd("%s:D:C" % papel, date(h.data, 'Ymd'), key_c)
            r.zadd("%s:D:H" % papel, date(h.data, 'Ymd'), key_h)
            r.zadd("%s:D:L" % papel, date(h.data, 'Ymd'), key_l)
            r.zadd("%s:D:V" % papel, date(h.data, 'Ymd'), key_v)
            if ttl > 0:
                r.expire(key_o, ttl)
                r.expire(key_c, ttl)
                r.expire(key_h, ttl)
                r.expire(key_l, ttl)
                r.expire(key_v, ttl)
                r.expire("%s:D:O" % papel, ttl)
                r.expire("%s:D:C" % papel, ttl)
                r.expire("%s:D:H" % papel, ttl)
                r.expire("%s:D:L" % papel, ttl)
                r.expire("%s:D:V" % papel, ttl)
        elif periodo == 'S':
            key = h.data.strftime('%Y%W')

            papel = h.papel.codigo
            key_o = '%s:S:%s:O' % (papel, key)
            key_c = '%s:S:%s:C' % (papel, key)
            key_h = '%s:S:%s:H' % (papel, key)
            key_l = '%s:S:%s:L' % (papel, key)
            key_v = '%s:S:%s:V' % (papel, key)

            if not r.exists(key_o):
                r.set(key_o, h.preabe)
                r.set(key_h, h.premax)
                r.set(key_l, h.premin)
                r.set(key_v, h.voltot)
            else:
                r.set(key_v, (h.voltot + Decimal(r.get(key_v))))

                maxima = Decimal(r.get(key_h))
                if h.premax > maxima:
                    r.set(key_h, h.premax)

                minima = Decimal(r.get(key_l))
                if h.premin < minima:
                    r.set(key_l, h.premin)

            r.set(key_c, h.preult)

            r.zadd("%s:S:O" % papel, key, key_o)
            r.zadd("%s:S:C" % papel, key, key_c)
            r.zadd("%s:S:H" % papel, key, key_h)
            r.zadd("%s:S:L" % papel, key, key_l)
            r.zadd("%s:S:V" % papel, key, key_v)
            if ttl > 0:
                r.expire(key_o, ttl)
                r.expire(key_c, ttl)
                r.expire(key_h, ttl)
                r.expire(key_l, ttl)
                r.expire(key_v, ttl)
                r.expire("%s:S:O" % papel, ttl)
                r.expire("%s:S:C" % papel, ttl)
                r.expire("%s:S:H" % papel, ttl)
                r.expire("%s:S:L" % papel, ttl)
                r.expire("%s:S:V" % papel, ttl)

        elif periodo == 'M':
            key = h.data.strftime('%Y%m')

            papel = h.papel.codigo
            key_o = '%s:M:%s:O' % (papel, key)
            key_c = '%s:M:%s:C' % (papel, key)
            key_h = '%s:M:%s:H' % (papel, key)
            key_l = '%s:M:%s:L' % (papel, key)
            key_v = '%s:M:%s:V' % (papel, key)

            if not r.exists(key_o):
                r.set(key_o, h.preabe)
                r.set(key_h, h.premax)
                r.set(key_l, h.premin)
                r.set(key_v, h.voltot)
            else:
                r.set(key_v, (h.voltot + Decimal(r.get(key_v))))

                maxima = Decimal(r.get(key_h))
                if h.premax > maxima:
                    r.set(key_h, h.premax)

                minima = Decimal(r.get(key_l))
                if h.premin < minima:
                    r.set(key_l, h.premin)

            r.set(key_c, h.preult)

            r.zadd("%s:M:O" % papel, key, key_o)
            r.zadd("%s:M:C" % papel, key, key_c)
            r.zadd("%s:M:H" % papel, key, key_h)
            r.zadd("%s:M:L" % papel, key, key_l)
            r.zadd("%s:M:V" % papel, key, key_v)

            if ttl > 0:
                r.expire(key_o, ttl)
                r.expire(key_c, ttl)
                r.expire(key_h, ttl)
                r.expire(key_l, ttl)
                r.expire(key_v, ttl)
                r.expire("%s:M:O" % papel, ttl)
                r.expire("%s:M:C" % papel, ttl)
                r.expire("%s:M:H" % papel, ttl)
                r.expire("%s:M:L" % papel, ttl)
                r.expire("%s:M:V" % papel, ttl)


    def historico_to_redis_diario(self, codigo_papel, ttl=0):
        from bovespa.models import Historico

        historicos = Historico.objects.filter(papel__codigo=codigo_papel).order_by('data')
        historicos_total = historicos.count()

        if historicos_total > 250:
            historicos = historicos[historicos_total-250:historicos_total]
            historicos_total = 250

        logger.debug("Valores diarios para %s - historicos: %s" % (codigo_papel, historicos_total))

        for h in historicos:
            self.historico_to_redis(h, 'D', ttl)


    def historico_to_redis_semanal(self, codigo_papel, ttl=0):
        """VERSAO ANTIGA
        from bovespa.models import Historico
        historicos = Historico.objects.filter(papel__codigo=codigo_papel).order_by('data')
        historicos_total = historicos.count()
        if historicos_total > 1400:
            historicos = historicos[historicos_total-1400:historicos_total]
            historicos_total = 1400
        logger.debug("Valores semanais para %s - historicos: %s" % (codigo_papel, historicos_total))
        for h in historicos:
            self.historico_to_redis(h, 'S', ttl)
        """
        query =  """
        select
        YEARWEEK(data) as semana, 
        max(premax), 
        min(premin),
        SUBSTRING_INDEX( GROUP_CONCAT(CAST(preabe AS CHAR) ORDER BY data), ',', 1 ) as abertura,
        SUBSTRING_INDEX( GROUP_CONCAT(CAST(preult AS CHAR) ORDER BY data DESC), ',', 1 ) as fechamento,
        sum(voltot)
        from bovespa_historico bh
        where papel_id = '%s'
        group by YEARWEEK(data)
        order by YEARWEEK(data) DESC
        limit 0, 300;
        """ % codigo_papel

        cursor = connection.cursor()
        cursor.execute(query)
        linhas = cursor.fetchall()

        for linha in linhas:

            anosemana  = linha[0]
            maxima     = linha[1]
            minima     = linha[2]
            abertura   = linha[3]
            fechamento = linha[4]
            volume     = linha[5]

            papel = codigo_papel
            key = anosemana

            key_o = '%s:S:%s:O' % (papel, key)
            key_c = '%s:S:%s:C' % (papel, key)
            key_h = '%s:S:%s:H' % (papel, key)
            key_l = '%s:S:%s:L' % (papel, key)
            key_v = '%s:S:%s:V' % (papel, key)

            self.r.set(key_h, maxima)
            self.r.set(key_l, minima)
            self.r.set(key_o, abertura)
            self.r.set(key_c, fechamento)
            self.r.set(key_v, volume)

            self.r.zadd("%s:S:O" % papel, key, key_o)
            self.r.zadd("%s:S:C" % papel, key, key_c)
            self.r.zadd("%s:S:H" % papel, key, key_h)
            self.r.zadd("%s:S:L" % papel, key, key_l)
            self.r.zadd("%s:S:V" % papel, key, key_v)

            if ttl > 0:
                self.r.expire(key_o, ttl)
                self.r.expire(key_c, ttl)
                self.r.expire(key_h, ttl)
                self.r.expire(key_l, ttl)
                self.r.expire(key_v, ttl)
                self.r.expire("%s:S:O" % papel, ttl)
                self.r.expire("%s:S:C" % papel, ttl)
                self.r.expire("%s:S:H" % papel, ttl)
                self.r.expire("%s:S:L" % papel, ttl)
                self.r.expire("%s:S:V" % papel, ttl)


    def historico_to_redis_mensal(self, codigo_papel, ttl=0):
        """ VERSÃO ANTIGA
        from bovespa.models import Historico
        historicos = Historico.objects.filter(papel__codigo=codigo_papel).order_by('data')
        historicos_total = historicos.count()
        if historicos_total > 3000:
            historicos = historicos[historicos_total-3000:historicos_total]
            historicos_total = 3000
        logger.debug("Valores mensais para %s - historicos: %s" % (codigo_papel, historicos_total))
        for h in historicos:
            self.historico_to_redis(h, 'M', ttl)
        """

        query =  """
        select year(data) as ano, 
        month(data) as mes, 
        max(premax), 
        min(premin),
        SUBSTRING_INDEX( GROUP_CONCAT(CAST(preabe AS CHAR) ORDER BY data), ',', 1 ) as abertura,
        SUBSTRING_INDEX( GROUP_CONCAT(CAST(preult AS CHAR) ORDER BY data DESC), ',', 1 ) as fechamento,
        sum(voltot)
        from bovespa_historico bh
        where papel_id = '%s'
        group by year(data), month(data)
        order by year(data) DESC, month(data) DESC
        limit 0, 300;
        """ % codigo_papel
#        (SELECT preabe ORDER BY data ASC LIMIT 1) abertura,
#        (SELECT preult ORDER BY data DESC LIMIT 1) fechamento,


        cursor = connection.cursor()
        cursor.execute(query)
        linhas = cursor.fetchall()

        for linha in linhas:

            ano        = linha[0]
            mes        = linha[1]
            maxima     = linha[2]
            minima     = linha[3]
            abertura   = linha[4]
            fechamento = linha[5]
            volume     = linha[6]

            papel = codigo_papel
            key = "%04d%02d" % (ano, mes)

            key_o = '%s:M:%s:O' % (papel, key)
            key_c = '%s:M:%s:C' % (papel, key)
            key_h = '%s:M:%s:H' % (papel, key)
            key_l = '%s:M:%s:L' % (papel, key)
            key_v = '%s:M:%s:V' % (papel, key)

            self.r.set(key_h, maxima)
            self.r.set(key_l, minima)
            self.r.set(key_o, abertura)
            self.r.set(key_c, fechamento)
            self.r.set(key_v, volume)

            self.r.zadd("%s:M:O" % papel, key, key_o)
            self.r.zadd("%s:M:C" % papel, key, key_c)
            self.r.zadd("%s:M:H" % papel, key, key_h)
            self.r.zadd("%s:M:L" % papel, key, key_l)
            self.r.zadd("%s:M:V" % papel, key, key_v)

            if ttl > 0:
                self.r.expire(key_o, ttl)
                self.r.expire(key_c, ttl)
                self.r.expire(key_h, ttl)
                self.r.expire(key_l, ttl)
                self.r.expire(key_v, ttl)
                self.r.expire("%s:M:O" % papel, ttl)
                self.r.expire("%s:M:C" % papel, ttl)
                self.r.expire("%s:M:H" % papel, ttl)
                self.r.expire("%s:M:L" % papel, ttl)
                self.r.expire("%s:M:V" % papel, ttl)


    def limpar_cache(self):
        keys = self.r.smembers(PAPEIS_CACHE)
        logger.info("Limpando cache: %i chaves removidas." % (len(keys)))
        for _k in keys:
            self.r.srem(PAPEIS_CACHE, _k)

