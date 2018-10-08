# import urllib.request
import logging
from configparser import ConfigParser
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logger = logging.getLogger(__name__)

'''
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
'''


class CutreronteTelegram:
    def __init__(self, token, log_group_id, general_group_id, security_group_id, estado_sitio, domoticz):
        self.estado_sitio = estado_sitio
        self.log_group_id = log_group_id
        self.general_group_id = general_group_id
        self.security_group_id = int(security_group_id)
        self.domoticz = domoticz

        # Start the bot.
        # Create the EventHandler and pass it your bot's token.
        updater = Updater(token)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher
        self.bot = dp.bot  # para poder mandar mensajes

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help))

        dp.add_handler(CommandHandler("users_in", self.users_in))
        dp.add_handler(CommandHandler("status", self.status))
        dp.add_handler(CommandHandler("cerrar", self.cerrar))
        dp.add_handler(CommandHandler("abrir", self.abrir))

        # on noncommand i.e message - echo the message on Telegram
        # dp.add_handler(MessageHandler(Filters.text, self.echo))

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        # updater.idle()

    def enviar_mensaje(self, texto, chatid):
        self.bot.send_message(chatid, text=texto)
        logging.info("Enviado por telegram: '{}'".format(texto))

    def enviar_estado_hangar(self):
        self.enviar_mensaje("Hangar 2 {}".format(self.estado_sitio.texto_abierto_cerrado.lower()), self.general_group_id)

    def enviar_usuario_entro(self, nombre):
        self.enviar_mensaje("{} acaba de entrar".format(nombre), self.log_group_id)

    def enviar_usuario_salio(self, nombre):
        self.enviar_mensaje("{} ha salido".format(nombre), self.log_group_id)

    def users_in(self, bot, update):
        """Send a message ...."""
        if self.estado_sitio.numero_usuarios > 0:
            msg = "{} personas: {}".format(self.estado_sitio.numero_usuarios, self.estado_sitio.listado_usuarios_string)
        elif self.estado_sitio.abierto_cerrado == True:
            msg = "Usuario anonimo"
        else:
            msg = "Nadie dentro"
        update.message.reply_text(msg)

    def status(self, bot, update):
        """Send a message ...."""
        update.message.reply_text("Hangar 2 {}".format(self.estado_sitio.texto_abierto_cerrado.lower()))

    def cerrar(self, bot, update):
        """Send a message ...."""
        if not self.autorizacion_segura(update, "cerrar"):
            return
        if self.estado_sitio.abierto_cerrado:
            if self.estado_sitio.numero_usuarios > 0:
                msg = "Expulsados {}. Hangar 2 Cerrado".format(self.estado_sitio.listado_usuarios_string)
                self.estado_sitio.vaciar_usuarios()
            self.estado_sitio.abierto_cerrado = False
            self.domoticz.desactivar()
            self.enviar_estado_hangar()
        else:
            self.domoticz.desactivar()  # por seguridad
            msg = "Ya esta cerrado"
        update.message.reply_text(msg)

    def abrir(self, bot, update):
        if not self.autorizacion_segura(update, "abrir"):
            return
        if not self.estado_sitio.abierto_cerrado:
            msg = "Hangar 2 Abierto (anonimo)"
            self.estado_sitio.abierto_cerrado = True
            self.domoticz.activar()
            self.enviar_estado_hangar()
        else:
            self.domoticz.desactivar()  # por seguridad
            msg = "Ya esta abierto"
        update.message.reply_text(msg)

    def start(self, bot, update):
        """Send a message when the command /start is issued."""
        update.message.reply_text('Hola!')
        self.help(bot, update)

    @staticmethod
    def help(bot, update):
        """Send a message when the command /help is issued."""
        update.message.reply_text('Los comandos disponibles son: /status /users_in /abrir /cerrar')

    @staticmethod
    def echo(bot, update):
        """Echo the user message."""
        update.message.reply_text(update.message.text)

    @staticmethod
    def error(bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)

    def autorizacion_segura(self, update, comando):
        """ Devuelve True si la peticion es de el grupo seguro """
        if update.message.chat.id != self.security_group_id:
            update.message.reply_text("no esta autorizado para usar esta funcion")
            logging.info("Intentado comando '{}' desde id '{}'. Operacion no permitida".format(comando, update.message.chat.id))
            return False
        else:
            return True


if __name__ == '__main__':
    """ Probar la Api """
    config = ConfigParser()
    config.read("config.ini")

    telegram_log_group = config.get('TELEGRAM', 'log_group', fallback='-111111')
    telegram_general_group = config.get('TELEGRAM', 'general_group', fallback='-111111')
    telegram_security_group = config.get('TELEGRAM', 'security_group', fallback='-111111')
    telegram_token = config.get('TELEGRAM', 'token', fallback='111111')

    tg = CutreronteTelegram(telegram_token, telegram_log_group, telegram_general_group, telegram_security_group,
                            None, None)
    tg.enviar_mensaje("Esto es una prueba", telegram_log_group)
    print("El script se queda esperando por comandos. CTRL+C para salir")
    tg.updater.idle()
