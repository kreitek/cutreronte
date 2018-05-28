class CutreronteTelegram():
    def __init__(self):
        pass

    def enviar_mensaje(self, mensaje):
        print("Enviado por telegram: '{}'".format(mensaje))


if __name__ == '__main__':
    """ Probar la Api """
    tg = CutreronteTelegram()
    tg.enviar_mensaje("Esto es una prueba")