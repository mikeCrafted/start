from flask import render_template, url_for, flash, redirect, request, make_response, jsonify
from flaskStart import app
from venv import EnvBuilder
import secrets, os

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create', methods = ['POST'])
def create():
    req = request.get_json()
    print(req)
    temp_dir = f"{app.root_path}\\generated\\{secrets.token_hex(16)}"
    project_dir = f"{temp_dir}\\{req['projectName']}"
    os.mkdir(temp_dir)
    os.mkdir(project_dir)
    os.mkdir(f"{project_dir}\\{req['projectName']}")
    # creating virtual environment
    if req['virtEnv']['show'] == True:
        virt_env_data = req['virtEnv']
        create_virt_env(name = virt_env_data['name'],
                        use_system_site_packages = virt_env_data['params'][0],
                        use_clear = virt_env_data['params'][1], 
                        use_with_pip = virt_env_data['params'][2],
                        target_dir = project_dir)
    # creating requirements file
    with open(f'{project_dir}\\requirements.txt', 'w') as f:
        for package in req['requirements']:
            f.write(f"{package['name']}{package['type']}{package['version']}\n")
    
    return make_response(jsonify('ok'), 200)

# DB
# from flaskblog import db
# from flaskblog.models import User, Post
# db.create_all()
# db.session.commit()

def create_virt_env(name, use_system_site_packages, use_clear, use_with_pip, target_dir):
    my_env_builder = EnvBuilder(system_site_packages = use_system_site_packages,
                                clear = use_clear, with_pip = use_with_pip)
    my_env_builder.create(f'{target_dir}\\{name}')