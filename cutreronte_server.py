from flask import Flask, render_template, redirect, url_for, request, flash
from flask_restful import Resource, Api, abort
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField
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
domoticz_idx_open = config.get('DOMOTICZ', 'idx_open', fallback='1')
domoticz_idx_pestillera = config.get('DOMOTICZ', 'idx_pestillera', fallback='2')


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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True  # adds significant overhead, desactivar cuando la app este madura
app.config['SECRET_KEY'] = app_secretkey

db = SQLAlchemy(app)
auth = HTTPBasicAuth()

tg = CutreronteTelegram(telegram_token)
dz = CutreronteDomoticz(domoticz_host, domoticz_port, domoticz_idx_open, domoticz_idx_pestillera)

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
    abiertocerradotexto = "ABIERTO" if su.abierto_cerrado else "CERRADO"
    return render_template('home.html', estado=abiertocerradotexto, nusuarios=len(su.usuarios_dentro))


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
        flash('Usuario {} actualizado'.format(u.username), 'success')
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
            if u.autorizado:
                su.alguien_entro_o_salio(u)  # uso rfid porque el nombre a veces es None
                actualiza_visto_por_ultima_vez(u)  # no modificar antes de comprobar si entro o salio
                # devuelve json si la peticion viene de fuera, o devuelve a listado usuarios si es interna
                if request.remote_addr == '127.0.0.1':
                    flash('Emulada tarjeta {}'.format(u.rfid), 'success')
                    return redirect(url_for('listar_usuarios'))
                else:
                    return {'status': 'ok', 'username': u.username}
            else:
                actualiza_visto_por_ultima_vez(u)
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
