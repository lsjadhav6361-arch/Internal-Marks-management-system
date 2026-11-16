from flask import Flask, flash, redirect, render_template, request, session, url_for

from utils.auth import verify_password

from config import Config
from database.db import get_db, init_db
from routes.admin_routes import admin
from routes.report_routes import report
from routes.student_routes import student
from routes.teacher_routes import teacher

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']
app.config['SESSION_PERMANENT'] = False
app.register_blueprint(admin)
app.register_blueprint(teacher)
app.register_blueprint(student)
app.register_blueprint(report)


@app.before_request
def keep_browser_session_temporary():
    session.permanent = False


@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_type = request.form.get('user_type')

        if user_type == 'admin_hod':
            # Admin/HOD login uses email/username and hashed passwords.  Only
            # accounts with role in ('admin', 'hod') are allowed.  We fetch
            # the record first and then verify the password using
            # ``verify_password`` to support both hashed and legacy plain
            # text passwords.
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '').strip()

            with app.app_context():
                with get_db() as conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(
                        """
                        SELECT id, role, username, display_name, password
                        FROM users
                        WHERE username = %s AND role IN ('admin', 'hod')
                        LIMIT 1
                        """,
                        (username,),
                    )
                    user = cursor.fetchone()
                    cursor.close()

            if not user or not verify_password(user['password'], password):
                flash('Invalid Admin / HOD credentials', 'error')
                return redirect(url_for('login'))

            session.clear()
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            session['display_name'] = user['display_name']
            flash(f"{user['role'].upper()} login successful", 'success')
            return redirect(url_for('admin.dashboard'))

        if user_type == 'teacher':
            username = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '').strip()

            with app.app_context():
                with get_db() as conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute(
                        """
                        SELECT id, name, email, phone, password
                        FROM teachers
                        WHERE email = %s
                        LIMIT 1
                        """,
                        (username,),
                    )
                    user = cursor.fetchone()
                    cursor.close()

            if not user:
                flash('Teacher not found', 'error')
                return redirect(url_for('login'))

            # Teachers may log in either with their password (hashed or plain)
            # or, as a fallback for legacy accounts, using their phone number
            # as the password.  The call to verify_password gracefully
            # handles both hashed and plain password values.
            valid_password = False
            if user.get('password'):
                valid_password = verify_password(user['password'], password)
            # fallback: allow phone number as password only if a phone is set
            if not valid_password and user.get('phone'):
                valid_password = (user['phone'] == password)

            if not valid_password:
                flash('Invalid teacher credentials', 'error')
                return redirect(url_for('login'))

            session.clear()
            session['teacher_id'] = user['id']
            session['display_name'] = user['name']
            session['user_role'] = 'teacher'
            flash('Teacher login successful', 'success')
            return redirect(url_for('teacher.dashboard'))

        if user_type == 'student':
            return redirect(url_for('student.login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    previous_role = session.get('user_role')
    session.clear()
    flash('Logged out successfully', 'success')
    if previous_role == 'student':
        return redirect(url_for('student.login'))
    return redirect(url_for('login'))


with app.app_context():
    init_db()


if __name__ == '__main__':
    app.run(debug=True)
