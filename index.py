#IMPORTACIONES NECESARIAS DE CLASES Y METODOS NECESARIOS
from flask import Flask, render_template,request,url_for,redirect,session
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

#IMPORTACION DE MODELS
from Models.models import db,Proyecto, Usuario, Tarea, Estado, Prioridad, Categoria

#IMPORTACION DE SETTINGS
from Settings.settings import get_sqlalchemy_uri

#IMPORTACIN DE CONTROLLERS
from Controllers.ctr_usuarios import CD_Usuario
from Controllers.ctr_categoria import Controll_Categoria
from Controllers.ctr_proyectos import Controll_Proyecto

#IMPORTACIN DE CONTROLLERS
from FireStore.fs_usuarios import CN_Usuarios
from FireStore.fs_categoria import categorias_listado,categoria_registrado
from FireStore.fs_proyectos import proyectos_listado,proyecto_registrado

#IMPORTACION DE SOURCES
from Sources.src_Recursos import CN_Recursos
from Sources.src_Correo import Enviar_correo
from Sources.src_rutas import login_required
from Sources.src_dashboard import Cantidades

#INICIALIZACION DE LA APP FLASK
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = get_sqlalchemy_uri()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'tu_clave_secreta'
db.init_app(app)
migrate = Migrate(app, db) 
ma = Marshmallow(app)

#GENERACION DE LOS MODELOS DE BASE DE DATOS
with app.app_context():
    db.create_all()

# ================================ RUTA RAIZ DIRIGIENDO A UNA RUTA ESPECIFICA ===============================
@app.route('/')
def home():
    return redirect(url_for('login'))
#============================================================================================================

# ================================ RUTA PARA EL LOGIN PRINCIPAL =============================================
#RUTA PARA REDIRIGIR AL LOGIN
@app.route('/login',methods=['GET', 'POST'] )
def login():
    return render_template('login.html')

#RUTA PARA ENVIAR DATOS 
@app.route('/enviar_datos', methods=['GET', 'POST'])
def enviar_datos():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        contraseña = CN_Recursos().convertir_hash(contraseña)
        usuario = CN_Usuarios().consultar_usuario(correo,contraseña)
        if usuario:
            print(usuario.id_usuario)
            session['id_usuario'] = usuario.id_usuario
            session['nombre_usuario'] = usuario.nombre_usuario
            session['correo_usuario'] = usuario.correo_usuario
            session['apellido_usuario'] = usuario.apellido_usuario
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login', mensaje='Correo o contraseña incorrectos'))
    return redirect(url_for('login'))

#RUTA PARA CERRAR LA SESSION
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login')) 
#============================================================================================================

# ================================ RUTA PARA LA SECCION INDEX  ==============================================
@app.route('/index')
def index():
    cd= CN_Usuarios()
    listar_usuarios= cd.usuarios_listado()
    correo = session.get('correo_usuario', 'Usuario no identificado')
    nombre = session.get('nombre_usuario', 'Usuario no identificado')
    apellido = session.get('apellido_usuario', 'Usuario no identificado')
    id_usuario = session.get('id_usuario') 
    categoria = Categoria.query.all()
    cantidad_proyectos = Cantidades().mostrar_proyectos(id_usuario)
    cantidad_tareas = Cantidades().mostrar_tareas(id_usuario)
    return render_template('index.html', listar_usuarios=listar_usuarios, correo=correo, 
                            nombre=nombre, apellido=apellido, categoria=categoria, id=id_usuario,cantidad_proyectos=cantidad_proyectos,cantidad_tareas=cantidad_tareas)
#============================================================================================================

# ================================ RUTA PARA LA SECCION REGISTRO ============================================
#RUTA PARA REDIRECCIONAR AL REGISTRO DE USUARIOS
@app.route('/registro_vista', methods=['GET', 'POST'])
def registro_vista():
    return render_template('registro.html')

#RUTA PARA REALIZAR EL REGISTRO
@app.route('/registro_usuario', methods=['GET', 'POST'])
def registro_usuario():
    mensaje = ""
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        conf_contraseña = request.form['conf_contraseña']

        mensaje_contraseña = CN_Usuarios().confirmar_contraseña(contraseña, conf_contraseña)
        if mensaje_contraseña:
            return render_template('registro.html', mensaje=mensaje_contraseña)

        obj_user = Usuario(
            nombre_usuario=nombre,
            apellido_usuario=apellido,
            correo_usuario=correo,
            contraseña_usuario=contraseña
        )
        mensaje = CN_Usuarios().usuario_registrado(obj_user)
        if mensaje == "usuario creado exitosamente":
            Enviar_correo(correo, contraseña)
            mensaje_bueno = "Felicidades, usuario creado exitosamente"
            return render_template('registro.html', mensaje=mensaje_bueno)
    return render_template('registro.html', mensaje=mensaje)
#============================================================================================================

# ================================= RUTA PARA LA CREAR CATEGORIA ============================================
@login_required
@app.route('/nueva_categoria', methods=['POST'])
def nueva_categoria():
    print('Creando categoria')
    if request.method == 'POST':
        nombreCat = request.form['nombreCat']
        obj_cat = Categoria(
            nombre_categoria=nombreCat,
        )
        print(obj_cat)
        mensaje = categoria_registrado(obj_cat)
        if mensaje == "categoria creado exitosamente":
            mensaje_bueno = "Felicidades, categoria creado exitosamente"
            db.session.add(obj_cat)
            db.session.commit()
            return redirect(url_for('index'))
    return render_template('index.html')
#============================================================================================================

# ================================== RUTA PARA LA CREAR PROYECTO ============================================
#RUTA PARA GENERAR UN NUEVO PROYECTO
@login_required
@app.route('/nuevo_proyecto', methods=['POST'])
def nuevo_proyecto():
    print('Entraste')
    if request.method == 'POST':
        titulo = request.form['tarea']
        descripcion = request.form['descripcion']
        categoria = request.form['mi_select']
        usuario = session.get('id_usuario')
        obj_proy = Proyecto(
            nombre_proyecto=titulo,
            descripcion_proyecto=descripcion,
            categoria_id=categoria,
            usuario_id_p=usuario,
        )
        print(obj_proy)
        mensaje = proyecto_registrado(obj_proy)
        if mensaje == "proyecto creado exitosamente":
            mensaje_bueno = "Felicidades, usuario creado exitosamente"
            db.session.add(obj_proy)
            db.session.commit()
            return render_template('index.html',mensaje=mensaje_bueno)
    return render_template('index.html')

# RUTA PARA LISTAR PROYECTO 
@login_required
@app.route('/proyectos', methods=['GET', 'POST'])
def proyectos():
    correo = session.get('correo_usuario', 'Usuario no identificado')
    nombre = session.get('nombre_usuario', 'Usuario no identificado')
    apellido = session.get('apellido_usuario', 'Usuario no identificado')
    categoria = Categoria.query.all()
    usuario_id = session.get('id_usuario')
    proyectos = Proyecto.query.filter_by(usuario_id_p=usuario_id).all()

    return render_template('proyectos.html', proyectos=proyectos,categoria=categoria,nombre=nombre,apellido=apellido)

#RUTA PARA MOSTRAR PROYECTO
@login_required
@app.route('/proyecto/<int:proyecto_id>')
def ver_proyecto(proyecto_id):
    correo = session.get('correo_usuario', 'Usuario no identificado')
    nombre = session.get('nombre_usuario', 'Usuario no identificado')
    apellido = session.get('apellido_usuario', 'Usuario no identificado')
    categoria = Categoria.query.all()
    proyecto = Proyecto.query.get_or_404(proyecto_id)
    print(proyecto.nombre_proyecto)
    print(proyecto.fcreacion_proyecto)
    print(proyecto_id)
    tareas = Tarea.query.filter_by(proyecto_id=proyecto_id).all()
    for ta in tareas:
        print(ta.titulo_tarea)
    cate = proyecto.categoria 
    print(cate.nombre_categoria)
    estado = Estado.query.all()
    print(estado)
    prioridad = Prioridad.query.all()
    return render_template('proyecto_detalle.html',categoria= categoria,nombre=nombre, apellido=apellido,estado=estado, prioridad=prioridad, proyecto=proyecto, tareas=tareas,cate=cate)
from datetime import datetime
@app.route('/nueva_tarea', methods=['POST'])
@login_required
def nueva_tarea():
    titulo = request.form['titulo']
    descripcion = request.form['descripcion']
    vencimiento_str = request.form['vencimiento']
    prioridad_id = request.form['prioridad_id']
    estado_id = request.form['estado_id']
    proyecto_id = request.form['proyecto_id']
    usuario_id = session.get('id_usuario')  # Asegúrate de que esté en sesión

    print("Título:", titulo)
    print("Descripción:", descripcion)
    print("Vencimiento:", vencimiento_str)
    print("Prioridad:", prioridad_id)
    print("Estado:", estado_id)
    print("Proyecto ID:", proyecto_id)
    print("Usuario ID:", usuario_id)
     # Convertir fecha string a datetime
    try:
        vencimiento = datetime.strptime(vencimiento_str, '%Y-%m-%d') if vencimiento_str else None
    except ValueError:
        print("La fecha no tiene un formato válido", "danger")
        return redirect(request.referrer)
    nueva_tarea = Tarea(
            titulo_tarea=titulo,
            descripcion_tarea=descripcion,
            fvencimiento_tarea=vencimiento,
            prioridad_id=prioridad_id,
            estado_id=estado_id,
            usuario_id=usuario_id,
            proyecto_id=proyecto_id
        )
    db.session.add(nueva_tarea)
    db.session.commit()
    return redirect(url_for('ver_proyecto', proyecto_id=proyecto_id))

# editar tarea
@app.route('/editar_tarea/<int:tarea_id>', methods=['POST'])
def editar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)  
    tarea.titulo_tarea = request.form['titulo']
    tarea.descripcion_tarea = request.form['descripcion']
    tarea.fvencimiento_tarea = request.form['vencimiento']
    tarea.prioridad_id = request.form['prioridad_id']
    tarea.estado_id = request.form['estado_id']
    tarea.proyecto_id = request.form['proyecto_id']
    db.session.commit()
    return redirect(url_for('ver_proyecto', proyecto_id=tarea.proyecto_id))

#eliminar tarea
@app.route('/eliminar_tarea/<int:tarea_id>', methods=['POST'])
@login_required
def eliminar_tarea(tarea_id):
    tarea = Tarea.query.get_or_404(tarea_id)
    proyecto_id = tarea.proyecto_id  

    db.session.delete(tarea)
    db.session.commit()
    return redirect(url_for('ver_proyecto', proyecto_id=proyecto_id))


#============================================================================================================

if __name__ == '__main__':
    app.run(debug=True, port=9000)


