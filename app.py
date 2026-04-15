from flask import Flask, render_template, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import psycopg
import psycopg.rows

app = Flask(__name__)

app.config['PROPAGATE_EXCEPTIONS'] = True
app.secret_key = 'techserv_secret_2025'

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'


# 🔥 DATABASE
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL no está configurada en Render")


def get_db_connection():
    return psycopg.connect(
        DATABASE_URL,
        sslmode="require",
        connect_timeout=10
    )


# ── Decoradores ──────────────────────────────────────────────
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


# ── HOME ─────────────────────────────────────────────────────
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)

        cur.execute("SELECT * FROM servicios WHERE activo = TRUE")
        servicios = cur.fetchall()

        cur.close()
        conn.close()

        return str(servicios)

    except Exception as e:
        return f"ERROR REAL ❌ {repr(e)}"


# ── LOGIN TEST DB (DEBUG OPCIONAL) ───────────────────────────
@app.route('/ping-db')
def ping_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        data = cur.fetchone()
        cur.close()
        conn.close()

        return f"DB OK ✅ {data}"

    except Exception as e:
        return f"DB ERROR ❌ {str(e)}"


# ── PING ─────────────────────────────────────────────────────
@app.route('/ping')
def ping():
    return "Flask está vivo ✅"


# ── REGISTRO ────────────────────────────────────────────────
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

    cur.execute("SELECT id FROM usuarios WHERE correo = %s", (correo,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'error': 'Correo ya registrado'}), 409

    hashed = generate_password_hash(contrasena)

    cur.execute(
        "INSERT INTO usuarios (nombre, telefono, correo, contrasena) VALUES (%s, %s, %s, %s) RETURNING id",
        (nombre, telefono, correo, hashed)
    )

    nuevo_id = cur.fetchone()['id']
    conn.commit()

    cur.close()
    conn.close()

    session['usuario_id'] = nuevo_id
    session['nombre'] = nombre
    session['correo'] = correo
    session['rol'] = 'usuario'

    return jsonify({'mensaje': f'Bienvenido {nombre}'})


# ── LOGIN ────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    correo = data.get('correo', '').strip().lower()
    contrasena = data.get('contrasena', '')

    conn = get_db_connection()
    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    cur.execute("SELECT * FROM usuarios WHERE correo = %s", (correo,))
    usuario = cur.fetchone()

    cur.close()
    conn.close()

    if not usuario or not check_password_hash(usuario['contrasena'], contrasena):
        return jsonify({'error': 'Credenciales incorrectas'}), 401

    session['usuario_id'] = usuario['id']
    session['nombre'] = usuario['nombre']
    session['correo'] = usuario['correo']
    session['rol'] = usuario['rol']

    return jsonify({'mensaje': f'Bienvenido {usuario["nombre"]}'})


# ── LOGOUT ───────────────────────────────────────────────────
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'mensaje': 'Sesión cerrada'})


# ── SESIÓN ───────────────────────────────────────────────────
@app.route('/api/sesion')
def sesion():
    if 'usuario_id' in session:
        return jsonify({
            'autenticado': True,
            'nombre': session['nombre'],
            'rol': session['rol']
        })
    return jsonify({'autenticado': False})


if __name__ == '__main__':
    app.run(debug=True)
