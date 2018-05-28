from flask import Flask, render_template, redirect, url_for, request
from flask_restful import Resource, Api, abort
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
from datetime import datetime
from cutreronte_seguimiento_usuarios import SeguimientoUsuarios


app = Flask(__name__, static_url_path="/static")
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cutreronte.db'
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245' # os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)
auth = HTTPBasicAuth()
su = SeguimientoUsuarios()


def actualiza_visto_por_ultima_vez(u):
    u.t_visto = datetime.now()
    db.update(Usuarios)
    db.session.commit()


@auth.verify_password
def verify_password(username, password):
    if username == 'test' and password == 'test':
        return True
    else:
        return False

class Usuarios(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)
    rfid = db.Column(db.String(11), unique=True, nullable=False)
    autorizado = db.Column(db.Boolean, unique=False, nullable=False)
    t_creacion = db.Column(db.TIMESTAMP, unique=False, nullable=False)
    t_visto = db.Column(db.TIMESTAMP, unique=False, nullable=False)


@app.route('/')
def home():
    return "Api de cutreronte"

@app.route('/usuarios')
def ListarUsuarios():
    lista = Usuarios.query.order_by(Usuarios.t_visto.desc()).all()
    lista_formateada = []
    for elemento in lista:
        el = {
            'id': elemento.id,
            'username': elemento.username if elemento.username else "NUEVO USUARIO!",
            'autorizado': elemento.autorizado,
            'autorizado_texto': "Autorizado" if elemento.autorizado else "Sin autorizar",
            't_creacion': elemento.t_creacion.strftime("%d-%m-%Y"),
            't_visto': elemento.t_visto.strftime("%d-%m-%Y %H:%M:%S")
        }
        lista_formateada.append(el)
    return render_template('lista.html', lista=lista_formateada)


@app.route("/autorizarusuario/<int:id>", methods=['GET'])
@auth.login_required
def autorizarusuario(id):
    u = Usuarios.query.filter_by(id=id).first()
    if u:
        setattr(u, 'autorizado', True)
        db.session.commit()
        #return "usuario {} autorizado".format(u.username)
        return redirect(url_for('ListarUsuarios'))
    else:
        abort(404, message='usuario no encontrado')



class FormUsuario(FlaskForm):
    username = StringField('Nombre', validators=[DataRequired()])
    autorizado = BooleanField('Autorizar')
    submit = SubmitField('Modificar')

@app.route("/modificarusuario/<int:id>", methods=['GET', 'POST'])
@auth.login_required
def modificar_usuario(id):
    u = Usuarios.query.filter_by(id=id).first()
    if not u:
        abort(404, message='usuario no encontrado')
    form = FormUsuario()
    if form.validate_on_submit():
        u.username = form.username.data
        u.autorizado = form.autorizado.data
        db.session.commit()
        return redirect(url_for('ListarUsuarios'))
    elif request.method == 'GET':
        form.username.data = u.username
        form.autorizado.data = True # por defecto check activado
        return render_template('editar_usuario.html', form=form, user=u)
    else:
        abort(404, message='usuario no encontrado')


class api1(Resource):
    @auth.login_required
    def get(self, rfid):
        u = Usuarios.query.filter_by(rfid=rfid).first()
        if u:  # el usuario ya existe
            print('username', u.username)
            actualiza_visto_por_ultima_vez(u)
            if u.autorizado:
                su.alguien_entro_o_salio(rfid)  # uso rfid porque el nombre a veces es None
                return {'status': 'ok', 'username': u.username}
            else:
                abort(401, message='no autorizado')
        else:  # un nuevo usuario
            nueva_tarjeta = Usuarios(username=None, rfid=rfid, autorizado=False,
                                     t_creacion=datetime.now(), t_visto=datetime.now())
            db.session.add(nueva_tarjeta)
            db.session.commit()
            abort(404, message='usuario no encontrado')

api.add_resource(api1, '/api/1/<rfid>')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)