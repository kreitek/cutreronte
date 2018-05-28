from cutreronte_domoticz import CutreronteDomoticz
from cutreronte_telegram import CutreronteTelegram
from time import sleep


class SeguimientoUsuarios():
    """ Lleva un control de los usuarios que entran y salen, da la señal de abierto y cerrado en domoticz
    y publica abierto cerrado en telegram """

    def __init__(self):
        self._usuarios_dentro = set()
        self.abierto_cerrado = False
        self.dz = CutreronteDomoticz()
        self.tg = CutreronteTelegram()

    @property
    def usuarios_dentro(self):
        return tuple(self._usuarios_dentro)

    def alguien_entro_o_salio(self, alguien):
        if alguien in self._usuarios_dentro:
            self._usuarios_dentro.remove(alguien)
        else:
            self._usuarios_dentro.add(alguien)
        self._comprobar_lleno_o_vacio()

    def _comprobar_lleno_o_vacio(self):
        if not self._usuarios_dentro and self.abierto_cerrado:
            print("Hangar 2 Cerrado")
            self.tg.enviar_mensaje("Hangar 2 Cerrado")
            self.dz.desactivar()
            self.abierto_cerrado = False

        elif self._usuarios_dentro and not self.abierto_cerrado:
            print("Hangar 2 Abierto")
            self.tg.enviar_mensaje("Hangar 2 Abierto")
            self.dz.activar()
            self.abierto_cerrado = True

    def echar_a_todos(self):
        self._usuarios_dentro.clear()
        self._comprobar_lleno_o_vacio()


if __name__ == '__main__':
    """ Probar la Api """
    su = SeguimientoUsuarios()
    su.alguien_entro_o_salio("FF.FF.FF.FF")
    print("En el espacio estan: {}".format(su.usuarios_dentro))
    sleep(3)
    su.alguien_entro_o_salio("CC.CC.CC.CC")
    print("En el espacio estan: {}".format(su.usuarios_dentro))
    sleep(3)
    su.alguien_entro_o_salio("FF.FF.FF.FF")
    print("En el espacio estan: {}".format(su.usuarios_dentro))
    sleep(3)
    su.echar_a_todos()
    print("En el espacio estan: {}".format(su.usuarios_dentro))
