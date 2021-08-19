from flask import render_template, request, make_response, jsonify
from flaskStart import app, SOURCES
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
    # creating temp directory so that multiple projects dont interfere
    os.mkdir(temp_dir)
    # creating root folder of project
    os.mkdir(project_dir)
    
    # creating run.py file
    create_run_file(project_dir, req['projectName'])
    
    # second level project folder for routes, blueprints etc.
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
    
    if req['blueprints']['show']:
        create_blueprints(req['blueprints'], project_dir)
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

def create_blueprints(blueprintsDict, project_dir):
    pass
    # create folder for each blueprint with routes and __init__ inside
    # register blueprint: admin_func = Blueprint('admin_func', __name__)
    # in global __init__: from minecratica.users_func.routes import users_func, and register blueprint: app.register_blueprint(users_func)


def create_run_file(project_dir, project_name):
    with open(f'{SOURCES}\\run.txt', 'r') as f:
        data = f.read()
    with open(f'{project_dir}\\run.py', 'w') as f:
        f.write(data.replace('[[ project_name ]]', project_name))