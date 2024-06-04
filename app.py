import os
import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session, jsonify
from werkzeug.exceptions import abort

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')

def get_db_connection():
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def get_post(post_id):
    conn = get_db_connection()
    if conn:
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
        conn.close()
        if post is None:
            abort(404)
        return post
    else:
        abort(500)

@app.route('/')
def index():
    conn = get_db_connection()
    if conn:
        posts = conn.execute('SELECT * FROM posts').fetchall()
        conn.close()
        return render_template('index.html', posts=posts)
    else:
        return "Error connecting to the database", 500

@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

@app.route('/create', methods=('GET', 'POST'))
def create():
    if 'loggedin' not in session:
        flash('You need to be logged in to create a post!')
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            if conn:
                try:
                    conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
                    conn.commit()
                except sqlite3.Error as e:
                    flash(f"An error occurred: {e}")
                finally:
                    conn.close()
                return redirect(url_for('index'))
            else:
                flash('Error connecting to the database')
    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    if 'loggedin' not in session:
        flash('You need to be logged in to edit a post!')
        return redirect(url_for('login'))
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()
            if conn:
                try:
                    conn.execute('UPDATE posts SET title = ?, content = ? WHERE id = ?', (title, content, id))
                    conn.commit()
                except sqlite3.Error as e:
                    flash(f"An error occurred: {e}")
                finally:
                    conn.close()
                return redirect(url_for('index'))
            else:
                flash('Error connecting to the database')
    return render_template('edit.html', post=post)

@app.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    if 'loggedin' not in session:
        return jsonify({'status': 'error', 'message': 'You need to be logged in to delete a post!'}), 403
    try:
        post = get_post(id)
        if post is None:
            return jsonify({'status': 'error', 'message': 'Post not found'}), 404
        conn = get_db_connection()
        if conn:
            conn.execute('DELETE FROM posts WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            flash(f'"{post["title"]}" was successfully deleted!')
            return redirect(url_for('index'))
        else:
            return jsonify({'status': 'error', 'message': 'Error connecting to the database'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # This is a simple and insecure way to check credentials.
        # Do not use this in a production environment.
        if username == 'admin' and password == 'sanuka':
            session['loggedin'] = True
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    flash('You have been logged out!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
