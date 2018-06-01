import urllib.request


class CutreronteTelegram:
    def __init__(self, token):
        self.token = token
        self.api_telegram = "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"


    def enviar_mensaje(self, texto, chatid):
        try:
            urllib.request.urlopen(self.api_telegram.format(self.token, chatid, texto))
            print("Enviado por telegram: '{}'".format(texto))
        except urllib.error.HTTPError:
            print("ha habido un error HTTPError")


if __name__ == '__main__':
    """ Probar la Api """
    tg = CutreronteTelegram("token")
    tg.enviar_mensaje("Esto es una prueba", "fsdf44534hf")