import urllib.request
import urllib.parse
from time import sleep
import logging

logger = logging.getLogger(__name__)

class CutreronteDomoticz:

    domoticz_api = "/json.htm?type=command&param=switchlight&idx={}&switchcmd={}"

    def __init__(self, host, port, idx):
        self.host = host
        self.port = port
        self.idx = idx
        # TODO con usuario y contraseña

    def activar(self):
        self._api_domoticz(True)

    def desactivar(self):
        self._api_domoticz(False)

    def _api_domoticz(self, encenderapagar):
        accion = "On" if encenderapagar else "Off"
        ruta = self.domoticz_api.format(self.idx, accion)
        url = 'http://{}:{}{}'.format(self.host, self.port, ruta)
        try:
            f = urllib.request.urlopen(url)
            # print(f.read().decode('utf-8'))
            status_code = f.getcode()
        except urllib.error.HTTPError as e:
            status_code = e
        if status_code != 200:
            logging.error("error, no se pudo hacer la peticion a domoticz. Status code: {}".format(status_code))


if __name__ == '__main__':
    """ Probar la Api """
    dz = CutreronteDomoticz("192.168.1.10", 8080, 1)
    dz.activar()
    print("Encendido")
    sleep(3)
    dz.desactivar()
    print("Apagado")
