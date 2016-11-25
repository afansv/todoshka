from flask import Flask, render_template, request, redirect, make_response
import rethinkdb as r
import uuid
import markdown

app = Flask(__name__)

conn = r.connect("localhost", 28015)

site_url = '127.0.0.1:5000'


@app.route('/')
@app.route('/index')
def index():
    username = request.cookies.get('username')
    notes = reversed(list(r.table("todos").filter(r.row["username"] == username).run(conn)))
    resp = make_response(render_template('index.html', notes=notes))
    if not username:
        resp.set_cookie('username', str(uuid.uuid4()))
    return resp


@app.route('/new', methods=['POST', 'GET'])
def new_note():
    note_name = request.form['noteName']
    note_content = request.form['noteContent']
    if not note_content:
        pass
    else:
        r.table('todos').insert({
            'note_name': note_name,
            'note_temp': note_content,
            'note_html': markdown.markdown(note_content, extensions=['markdown.extensions.nl2br']),
            'username': request.cookies.get('username'),
            'admin_token': str(uuid.uuid4()),
            'share_token': str(uuid.uuid4())
        }).run(conn)
    return redirect('/')


@app.route('/s/<admin_token>')
def s(admin_token):
    notes = list(r.table("todos").filter(r.row["admin_token"] == admin_token).run(conn))
    return render_template('manage.html', note=notes[0])


@app.route('/update/<admin_token>', methods=['POST', 'GET'])
def update(admin_token):
    todo = request.form['todo']
    r.table('todos').update({
        'note_temp': todo,
        'note_html': markdown.markdown(todo),
        'admin_token': admin_token
    }).run(conn)
    return redirect('/')


@app.route('/delete/<admin_token>', methods=['POST', 'GET'])
def delete(admin_token):
    r.table('todos').filter(r.row["admin_token"] == admin_token).delete().run(conn)
    return redirect('/')


@app.route('/note/<share_token>')
def get_note(share_token):
    notes = list(r.table('todos').filter(r.row['share_token'] == share_token).run(conn))
    return render_template('note.html', note = notes[0])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')