from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EstadoSitio:
    """ Lleva un control de los usuarios que entran y salen """
    def __init__(self):
        self._usuarios_dentro = set()  # objetos de la clase Usuario
        self.abierto_cerrado = False  # necesario para _comprobar_lleno_o_vacio

    @property
    def listado_usuarios(self):
        return [usuario.username for usuario in self._usuarios_dentro]

    @property
    def listado_usuarios_string(self):
        lista = ', '.join(self.listado_usuarios)
        return lista.replace("@", "")

    @property
    def numero_usuarios(self):
        return len(self._usuarios_dentro)

    @property
    def texto_abierto_cerrado(self):
        return "ABIERTO" if self.abierto_cerrado else "CERRADO"

    def esta_dentro(self, usuario):
        for u in self._usuarios_dentro:
            if u.rfid == usuario.rfid:
                return True
        return False

    def sacar(self, usuario):
        for u in self._usuarios_dentro:
            if u.rfid == usuario.rfid:
                self._usuarios_dentro.remove(u)
                break

    def meter(self, usuario):
        self._usuarios_dentro.add(usuario)

    def vaciar_usuarios(self):
        self._usuarios_dentro.clear()
        # NO pasar abierto_cerrado a False aqui


class SeguimientoUsuarios:
    """ Actualiza EstadoSitio, da la señal de abierto y cerrado en domoticz y publica abierto cerrado en telegram """
    def __init__(self, telegraminstance, domoticzinstance, estado_sitio):
        self.estado_sitio = estado_sitio
        self.dz = domoticzinstance
        self.tg = telegraminstance

    def alguien_entro_o_salio(self, usuario):
        # comprobamos que no ha vuelto a pasar la tarjeta imnediatamente
        if (datetime.now() - usuario.t_visto).seconds < 60:  # un minuto (antirrebotes)
            return
        # si estaba dentro lo saca, si no lo mete
        if self.estado_sitio.esta_dentro(usuario):
            self.estado_sitio.sacar(usuario)
            self.tg.enviar_usuario_salio(usuario.username)
            self.dz.pestillera()
        else:
            self.estado_sitio.meter(usuario)
            self.tg.enviar_usuario_entro(usuario.username)
            self.dz.pestillera()
        # comprueba si es el primero o el ultimo, para abrir o cerrar
        self._comprobar_lleno_o_vacio()

    def _comprobar_lleno_o_vacio(self):
        """ comprueba si es el primero o el ultimo, para abrir o cerrar """
        if self.estado_sitio.numero_usuarios < 1 and self.estado_sitio.abierto_cerrado:
            logging.info("Hangar 2 Cerrado")
            self.dz.desactivar()
            self.estado_sitio.abierto_cerrado = False
            self.tg.enviar_estado_hangar()
        elif self.estado_sitio.numero_usuarios > 0 and not self.estado_sitio.abierto_cerrado:
            logging.info("Hangar 2 Abierto")
            self.dz.activar()
            self.estado_sitio.abierto_cerrado = True
            self.tg.enviar_estado_hangar()

    def echar_a_todos(self):
        self.estado_sitio.vaciar_usuarios()
        self._comprobar_lleno_o_vacio()
