from flask import Flask, request, render_template_string, redirect, make_response, session
import sqlite3
import secrets

app = Flask(__name__)
# Clave secreta para firmar la sesión (mitiga manipulación de cookies)
app.secret_key = secrets.token_hex(32)


def db_query(query, params=()):
    """Ejecuta consultas con parámetros (mitiga SQL Injection)."""
    conn = sqlite3.connect('vulnerable.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.commit()
    conn.close()
    return result


def generar_csrf_token():
    """Genera o reutiliza un token CSRF por sesión."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']


def validar_csrf_token():
    """Valida el token CSRF enviado en el formulario."""
    token_form = request.form.get('csrf_token')
    token_sesion = session.get('csrf_token')
    return token_form and token_sesion and secrets.compare_digest(token_form, token_sesion)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username', '')
        pw = request.form.get('password', '')

        # MITIGACIÓN SQLi: consulta parametrizada
        usuarios = db_query(
            "SELECT * FROM usuarios WHERE username = ? AND password = ?",
            (user, pw)
        )

        if usuarios:
            usuario = usuarios[0]
            session.clear()
            session['user'] = usuario['username']
            generar_csrf_token()
            resp = make_response(redirect('/dashboard'))
            # MITIGACIÓN cookie: HttpOnly + SameSite (no exponer sesión en JS / CSRF básico)
            resp.set_cookie(
                'user_session',
                usuario['username'],
                httponly=True,
                samesite='Lax'
            )
            return resp
        return "<h3>Acceso denegado</h3><a href='/login'>Volver</a>", 401

    return '''
        <h2>Login del Sistema Académico</h2>
        <form method="post">
            Usuario: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Ingresar">
        </form>
    '''


@app.route('/dashboard')
def dashboard():
    username = session.get('user') or request.cookies.get('user_session')
    if not username:
        return redirect('/login')

    # MITIGACIÓN SQLi también en lecturas
    filas = db_query("SELECT * FROM usuarios WHERE username = ?", (username,))
    if not filas:
        return redirect('/login')
    datos = filas[0]
    csrf_token = generar_csrf_token()

    # MITIGACIÓN XSS: Jinja escapa {{ variables }} automáticamente
    html = """
    <h1>Panel de {{ username }}</h1>
    <p><b>Rol:</b> {{ rol }}</p>
    <p><b>Biografía:</b> {{ bio }}</p>
    <hr>
    <h3>Actualizar Biografía</h3>
    <form action="/update_bio" method="POST">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <input type="text" name="nueva_bio" placeholder="Escribe algo...">
        <input type="submit" value="Guardar Cambios">
    </form>
    <br><a href="/logout">Cerrar Sesión</a>
    """
    return render_template_string(
        html,
        username=datos['username'],
        rol=datos['rol'],
        bio=datos['bio'],
        csrf_token=csrf_token
    )


@app.route('/update_bio', methods=['POST'])
def update_bio():
    username = session.get('user') or request.cookies.get('user_session')
    if not username:
        return redirect('/login')

    # MITIGACIÓN CSRF: exigir token válido
    if not validar_csrf_token():
        return "<h3>Solicitud rechazada: token CSRF inválido</h3><a href='/dashboard'>Volver</a>", 403

    nueva_bio = request.form.get('nueva_bio', '')
    # MITIGACIÓN SQLi en UPDATE
    db_query(
        "UPDATE usuarios SET bio = ? WHERE username = ?",
        (nueva_bio, username)
    )
    return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect('/login'))
    resp.set_cookie('user_session', '', expires=0)
    return resp


@app.route('/')
def home():
    return redirect('/login')


if __name__ == '__main__':
    # MITIGACIÓN: debug desactivado
    app.run(debug=False, port=5000)
