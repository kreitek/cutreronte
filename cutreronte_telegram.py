import urllib.request
import logging

logger = logging.getLogger(__name__)


class CutreronteTelegram:
    def __init__(self, token):
        self.token = token
        self.api_telegram = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"

    def enviar_mensaje(self, texto, chatid):
        try:
            urllib.request.urlopen(self.api_telegram.format(self.token, chatid, texto), timeout=2)
            logging.info("Enviado por telegram: '{}'".format(texto))
        except UnicodeEncodeError:
            # 'ascii' codec can't encode character '\xf3' in position 112: ordinal not in range(128)
            self.enviar_mensaje(texto.encode('ascii', errors='replace').decode('ascii'), chatid)
        except Exception as e:
            logging.error(e)


if __name__ == '__main__':
    """ Probar la Api """
    tg = CutreronteTelegram("token")
    tg.enviar_mensaje("Esto es una prueba", "fsdf44534hf")
