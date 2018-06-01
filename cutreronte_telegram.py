import urllib.request
import logging

logger = logging.getLogger(__name__)

class CutreronteTelegram:
    def __init__(self, token):
        self.token = token
        self.api_telegram = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"


    def enviar_mensaje(self, texto, chatid):
        try:
            urllib.request.urlopen(self.api_telegram.format(self.token, chatid, texto))
            logging.info("Enviado por telegram: '{}'".format(texto))
        except urllib.error.HTTPError:
            logging.error("ha habido un error HTTPError")


if __name__ == '__main__':
    """ Probar la Api """
    tg = CutreronteTelegram("token")
    tg.enviar_mensaje("Esto es una prueba", "fsdf44534hf")