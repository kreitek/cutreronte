from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EstadoSitio:
    """ Lleva un control de los usuarios que entran y salen """
    def __init__(self):
        self.usuarios_dentro = set()  # objetos de la clase Usuario
        self.abierto_cerrado = False # necesario para comprobar si se abre por primera vez o se cierra al salir el ultimo

    @property
    def listado_usuarios(self):
        return [usuario.username for usuario in self.usuarios_dentro]

    @property
    def listado_usuarios_string(self):
        lista = ', '.join(self.listado_usuarios)
        return lista.replace("@", "")

    @property
    def numero_usuarios(self):
        return len(self.usuarios_dentro)

    @property
    def texto_abierto_cerrado(self):
        return "ABIERTO" if self.abierto_cerrado else "CERRADO"

    def vaciar_usuarios(self):
        self.usuarios_dentro.clear()
        # NO pasar abierto_cerrado a False aqui


class SeguimientoUsuarios:
    """ Actualiza EstadoSitio, da la señal de abierto y cerrado en domoticz y publica abierto cerrado en telegram """
    def __init__(self, telegraminstance, domoticzinstance, estado_sitio):
        self.estado_sitio = estado_sitio
        self.dz = domoticzinstance
        self.tg = telegraminstance

    def alguien_entro_o_salio(self, usuario):
        # comprobamos que no ha vuelto a pasar la tarjeta imnediatamente
        if (datetime.now() - usuario.t_visto).seconds < 90:  # minuto y medio
            return
        # si estaba dentro lo saca, si no lo mete
        if usuario in self.estado_sitio.usuarios_dentro:
            self.estado_sitio.usuarios_dentro.remove(usuario)
            self.tg.enviar_usuario_salio(usuario.username)
            self.dz.pestillera()
        else:
            self.estado_sitio.usuarios_dentro.add(usuario)
            self.tg.enviar_usuario_entro(usuario.username)
            self.dz.pestillera()
        # comprueba si es el primero o el ultimo, para abrir o cerrar
        self._comprobar_lleno_o_vacio()

    def _comprobar_lleno_o_vacio(self):
        """ comprueba si es el primero o el ultimo, para abrir o cerrar """
        if not self.estado_sitio.usuarios_dentro and self.estado_sitio.abierto_cerrado:
            logging.info("Hangar 2 Cerrado")
            self.dz.desactivar()
            self.estado_sitio.abierto_cerrado = False
            self.tg.enviar_estado_hangar()
        elif self.estado_sitio.usuarios_dentro and not self.estado_sitio.abierto_cerrado:
            logging.info("Hangar 2 Abierto")
            self.dz.activar()
            self.estado_sitio.abierto_cerrado = True
            self.tg.enviar_estado_hangar()

    def echar_a_todos(self):
        self.estado_sitio.vaciar_usuarios()
        self._comprobar_lleno_o_vacio()
