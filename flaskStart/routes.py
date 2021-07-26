from flask import render_template, url_for, flash, redirect, request, make_response, jsonify
from flaskStart import app
from venv import EnvBuilder

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods = ['POST'])
def create():
    req = request.get_json()
    print(req)
    # create_virt_env()
    return make_response(jsonify('ok'), 200)

# DB
# from flaskblog import db
# from flaskblog.models import User, Post
# db.create_all()
# db.session.commit()
def create_virt_env():
    my_env_builder = EnvBuilder(system_site_packages = False, clear = False, with_pip = True)
    my_env_builder.create(r'C:\Users\Michael\Desktop\venv')