from flask import Flask, render_template, redirect, url_for, request
from flask_restful import Resource, Api, abort
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
from datetime import datetime
from cutreronte_seguimiento_usuarios import SeguimientoUsuarios
from configparser import ConfigParser
from cutreronte_telegram import CutreronteTelegram
from cutreronte_domoticz import CutreronteDomoticz
import logging
from logging.handlers import TimedRotatingFileHandler
import os


config = ConfigParser()
config.read("config.ini")

app_user = config.get('APP', 'user', fallback='admin')
app_password = config.get('APP', 'password', fallback='admin')
app_secretkey = config.get('APP', 'secretkey', fallback='5791628bb0b13ce0c676dfde280ba245')
app_debug_level = config.get('APP', 'debug_level', fallback='INFO')

telegram_log_group = config.get('TELEGRAM', 'log_group', fallback='-111111')
telegram_general_group = config.get('TELEGRAM', 'general_group', fallback='-111111')
telegram_token = config.get('TELEGRAM', 'token', fallback='111111')

domoticz_host = config.get('DOMOTICZ', 'host', fallback='192.168.1.10')
domoticz_port = config.get('DOMOTICZ', 'port', fallback='8080')
domoticz_idx = config.get('DOMOTICZ', 'idx', fallback='1')

# si no existe directorio 'logs' lo crea
try:
    os.stat('logs')
except:
    os.mkdir('logs')

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-7.7s] %(message)s", "%H:%M:%S")
logger = logging.getLogger()
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
# logfilename = datetime.today().strftime("%Y%m%d%S")
# fileHandler = logging.FileHandler("logs/{}.log".format(logfilename))
fileHandler = TimedRotatingFileHandler("logs/cutreronte.log",  when='midnight')
fileHandler.suffix = "%Y%m%d.log"
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)
logger.setLevel(app_debug_level)


app = Flask(__name__, static_url_path="/static")
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cutreronte.db'
app.config['SECRET_KEY'] = app_secretkey

db = SQLAlchemy(app)
auth = HTTPBasicAuth()

tg = CutreronteTelegram(telegram_token)
dz = CutreronteDomoticz(domoticz_host, domoticz_port, domoticz_idx)

su = SeguimientoUsuarios(tg, dz, telegram_log_group, telegram_general_group)


def actualiza_visto_por_ultima_vez(u):
    u.t_visto = datetime.now()
    db.update(Usuarios)
    db.session.commit()


@auth.verify_password
def verify_password(username, password):
    return True if username == app_user and password == app_password else False


class Usuarios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    rfid = db.Column(db.String(11), unique=True, nullable=False)
    autorizado = db.Column(db.Boolean, unique=False, nullable=False)
    t_creacion = db.Column(db.TIMESTAMP, unique=False, nullable=False)
    t_visto = db.Column(db.TIMESTAMP, unique=False, nullable=False)


@app.route('/')
def home():
    respuesta = "<H1>Cutreronte</H1>"
    abiertocerradotexto = "ABIERTO" if su.abierto_cerrado else "CERRADO"
    respuesta += "<P>Espacio {}</P>".format(abiertocerradotexto)
    if su.abierto_cerrado:
        respuesta += "<P>Numero de usuarios dento: {}</P>".format(len(su.usuarios_dentro))
    return respuesta


@app.route('/usuarios')
@auth.login_required
def listar_usuarios():
    lista = Usuarios.query.order_by(Usuarios.t_visto.desc()).all()
    lista_formateada = []
    for elemento in lista:
        el = {
            'id': elemento.id,
            'username': elemento.username if elemento.username else "NUEVO USUARIO!",
            'rfid': elemento.rfid,
            'autorizado': elemento.autorizado,
            'autorizado_texto': "Autorizado" if elemento.autorizado else "Sin autorizar",
            't_creacion': elemento.t_creacion.strftime("%d-%m-%Y"),
            't_visto': elemento.t_visto.strftime("%d-%m-%Y %H:%M:%S")
        }
        lista_formateada.append(el)
    return render_template('lista.html', lista=lista_formateada)


class FormUsuario(FlaskForm):
    username = StringField('Nombre', validators=[DataRequired()])
    autorizado = BooleanField('Autorizar')
    submit = SubmitField('Modificar')


@app.route("/modificarusuario/<int:id_usuario>", methods=['GET', 'POST'])
@auth.login_required
def modificar_usuario(id_usuario):
    u = Usuarios.query.filter_by(id=id_usuario).first()
    if not u:
        abort(404, message='usuario no encontrado')
    form = FormUsuario()
    if form.validate_on_submit():
        u.username = form.username.data
        u.autorizado = form.autorizado.data
        db.session.commit()
        return redirect(url_for('listar_usuarios'))
    elif request.method == 'GET':
        form.username.data = u.username
        form.autorizado.data = True  # por defecto check activado
        return render_template('editar_usuario.html', form=form, user=u)
    else:
        abort(404, message='usuario no encontrado')


class Api1(Resource):
    @auth.login_required
    def get(self, rfid):
        u = Usuarios.query.filter_by(rfid=rfid).first()
        if u is not None:  # el usuario ya existe
            actualiza_visto_por_ultima_vez(u)
            if u.autorizado:
                su.alguien_entro_o_salio(u)  # uso rfid porque el nombre a veces es None
                return {'status': 'ok', 'username': u.username}
            else:
                abort(401, message='no autorizado')
        else:  # un nuevo usuario
            nueva_tarjeta = Usuarios(username=None, rfid=rfid, autorizado=False,
                                     t_creacion=datetime.now(), t_visto=datetime.now())
            db.session.add(nueva_tarjeta)
            db.session.commit()
            abort(404, message='usuario no encontrado')

api.add_resource(Api1, '/api/1/<rfid>')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
