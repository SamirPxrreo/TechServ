from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import psycopg
import psycopg.rows

app = Flask(__name__)
app.secret_key = 'techserv_secret_2025'

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ───────── DATABASE ─────────
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL no configurada")

def get_db_connection():
    return psycopg.connect(DATABASE_URL, sslmode="require")


# ───────── DECORADORES ─────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            return jsonify({'error': 'No autenticado'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session or session.get('rol') != 'admin':
            return redirect('/')
        return f(*args, **kwargs)
    return decorated


# ───────── HOME ─────────
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM servicios WHERE activo = TRUE")
    servicios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'index.html',
        servicios=servicios
    )


# ───────── ADMIN PANEL ─────────
@app.route('/admin')
@admin_required
def admin():
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    # stats
    cur.execute("SELECT COUNT(*) AS total FROM usuarios")
    total_usuarios = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) AS total FROM pedidos")
    total_pedidos = cur.fetchone()['total']

    cur.execute("SELECT COALESCE(SUM(total),0) AS ingresos FROM pedidos WHERE estado='completado'")
    ingresos = cur.fetchone()['ingresos']

    # pedidos
    cur.execute("""
        SELECT 
            p.id,
            p.total,
            p.estado,
            p.fecha,
            u.nombre,
            u.correo
        FROM pedidos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.id DESC
        LIMIT 20
    """)
    pedidos = cur.fetchall()

    # usuarios
    cur.execute("""
        SELECT *
        FROM usuarios
        ORDER BY id DESC
        LIMIT 20
    """)
    usuarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'admin.html',
        total_usuarios=total_usuarios,
        total_pedidos=total_pedidos,
        ingresos=ingresos,
        pedidos=pedidos,
        usuarios=usuarios
    )


# ───────── ADMIN: CAMBIAR ESTADO ─────────
@app.route('/api/admin/pedido/<int:id>', methods=['PUT'])
@admin_required
def cambiar_estado(id):
    data = request.json
    estado = data.get('estado')

    if estado not in ['pendiente', 'en proceso', 'completado', 'cancelado']:
        return jsonify({'error': 'Estado inválido'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE pedidos SET estado=%s WHERE id=%s RETURNING id",
        (estado, id)
    )

    updated = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    if not updated:
        return jsonify({'error': 'Pedido no encontrado'}), 404

    return jsonify({'ok': True})


# ───────── ADMIN: VER DETALLE ─────────
@app.route('/api/admin/pedido/<int:id>')
@admin_required
def detalle_pedido(id):
    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    # pedido
    cur.execute("""
        SELECT p.*, u.nombre, u.correo
        FROM pedidos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        WHERE p.id = %s
    """, (id,))
    pedido = cur.fetchone()

    if not pedido:
        cur.close()
        conn.close()
        return jsonify({'error': 'Pedido no encontrado'}), 404

    # items
    cur.execute("""
        SELECT nombre, precio, cantidad
        FROM pedido_items
        WHERE pedido_id = %s
    """, (id,))
    items = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        'pedido': pedido,
        'items': items
    })


# ───────── REGISTRO ─────────
@app.route('/api/registro', methods=['POST'])
def registro():
    data = request.json

    nombre = data.get('nombre', '').strip()
    telefono = data.get('telefono', '').strip()
    correo = data.get('correo', '').strip().lower()
    contrasena = data.get('contrasena', '')

    if not all([nombre, telefono, correo, contrasena]):
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT id FROM usuarios WHERE correo=%s", (correo,))
    if cur.fetchone():
        return jsonify({'error': 'Correo ya registrado'}), 409

    hashed = generate_password_hash(contrasena)

    cur.execute("""
        INSERT INTO usuarios (nombre, telefono, correo, contrasena, rol)
        VALUES (%s, %s, %s, %s, 'usuario')
        RETURNING id
    """, (nombre, telefono, correo, hashed))

    user_id = cur.fetchone()['id']
    conn.commit()

    cur.close()
    conn.close()

    session['usuario_id'] = user_id
    session['rol'] = 'usuario'

    return jsonify({'ok': True})


# ───────── LOGIN ─────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json

    correo = data.get('correo')
    contrasena = data.get('contrasena')

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or not check_password_hash(user['contrasena'], contrasena):
        return jsonify({'error': 'Credenciales incorrectas'}), 401

    session['usuario_id'] = user['id']
    session['rol'] = user['rol']

    return jsonify({'ok': True})


# ───────── LOGOUT ─────────
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})


# ───────── SESIÓN ─────────
@app.route('/api/sesion')
def sesion():
    if 'usuario_id' in session:
        return jsonify({
            'autenticado': True,
            'rol': session['rol']
        })

    return jsonify({'autenticado': False})


# ───────── CARRITO: AGREGAR ─────────
@app.route('/api/carrito/agregar', methods=['POST'])
@login_required
def carrito_agregar():
    data = request.json
    servicio_id = int(data.get('servicio_id'))

    if 'carrito' not in session:
        session['carrito'] = []

    carrito = session['carrito']

    for item in carrito:
        if item['id'] == servicio_id:
            item['cantidad'] += 1
            session.modified = True
            return jsonify({'ok': True})

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM servicios WHERE id=%s", (servicio_id,))
    servicio = cur.fetchone()

    cur.close()
    conn.close()

    carrito.append({
        'id': servicio['id'],
        'nombre': servicio['nombre'],
        'precio': float(servicio['precio']),
        'cantidad': 1
    })

    session.modified = True
    return jsonify({'ok': True})


# ───────── CARRITO: VER ─────────
@app.route('/api/carrito')
def carrito():
    return jsonify(session.get('carrito', []))


# ───────── CARRITO: CONFIRMAR ─────────
@app.route('/api/carrito/confirmar', methods=['POST'])
@login_required
def confirmar():
    carrito = session.get('carrito', [])
    data = request.json
    notas = data.get('notas', '')

    total = sum(i['precio'] * i['cantidad'] for i in carrito)

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("""
        INSERT INTO pedidos (usuario_id, total, notas, estado)
        VALUES (%s, %s, %s, 'pendiente')
        RETURNING id
    """, (session['usuario_id'], total, notas))

    pedido_id = cur.fetchone()['id']

    for item in carrito:
        cur.execute("""
            INSERT INTO pedido_items (pedido_id, nombre, precio, cantidad)
            VALUES (%s, %s, %s, %s)
        """, (pedido_id, item['nombre'], item['precio'], item['cantidad']))

    conn.commit()
    cur.close()
    conn.close()

    session['carrito'] = []

    return jsonify({'pedido_id': pedido_id})


if __name__ == '__main__':
    app.run(debug=True)
