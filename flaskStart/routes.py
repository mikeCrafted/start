from flask import render_template, request, make_response, jsonify
from flaskStart import app, SOURCES
from venv import EnvBuilder
import secrets, os, re
from flaskStart.helper_functions import *

@app.route('/')
def index():        
    return render_template('index.html')

@app.route('/create', methods = ['POST'])
def create():
    req = request.get_json()
    
    temp_dir = f"{app.root_path}\\generated\\{secrets.token_hex(16)}"
    project_dir = f"{temp_dir}\\{req['projectName']}"
    # creating temp directory so that multiple projects dont interfere
    os.mkdir(temp_dir)
    # creating root folder of project
    os.mkdir(project_dir)
    
    # creating run.py file
    create_run_file(project_dir, req['projectName'])
    
    # creating requirements file
    with open(f'{project_dir}\\requirements.txt', 'w') as f:
        for package in req['requirements']['packages']:
            f.write(f"{package['name']}{package['type']}{package['version']}\n")

    # second level project folder for routes, blueprints etc.
    project_dir = f"{project_dir}\\{req['projectName']}"
    os.mkdir(project_dir)
    
    # create templates folder
    os.mkdir(f"{project_dir}\\templates")
    # create static folder
    os.mkdir(f"{project_dir}\\static")

    if req['frontend']['show']:
        create_frontend(req['frontend'], project_dir, req['projectName'])
        

    # create main __init__ file
    create_init_file(req, project_dir)

    # creating virtual environment
    if req['virtEnv']['show'] == True:
        virt_env_data = req['virtEnv']
        create_virt_env(name = virt_env_data['name'],
                        use_system_site_packages = virt_env_data['params'][0],
                        use_clear = virt_env_data['params'][1], 
                        use_with_pip = virt_env_data['params'][2],
                        target_dir = project_dir)
    
    # get all forms
    if req['wtForms']['show']:
        wtForms = req['wtForms']
        if wtForms['asMainFile']:
            create_forms_file(wtForms['forms'], project_dir)

    if req['blueprints']['show']:
        create_blueprints(req['blueprints'], req['wtForms'], project_dir, req['projectName'])
    else:
        create_routes_file(req, project_dir)
    
    if req['addDatabase']:
        create_models_file(req, project_dir)

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

def create_blueprints(blueprintsDict, wtForms, project_dir, project_name):
    for_main_init = ''
    for blueprint in blueprintsDict['blueprintsList']:
        os.mkdir(f"{project_dir}\\{blueprint['name']}")
        with open(f"{project_dir}\\{blueprint['name']}\\__init__.py", 'w'): pass
        with open(f"{project_dir}\\{blueprint['name']}\\routes.py", 'w') as f:
            f.write(generate_blueprint_imports_string(project_name, blueprint['name']))
        for_main_init += f"from {project_name}.{blueprint['name']}.routes import {blueprint['name']}\n"
        for_main_init += f"app.register_blueprint({blueprint['name']})\n"
        if blueprint['addForms']:
            forms_list = [form for form in wtForms['forms'] if form['name'] in blueprint['forms']]
            create_forms_file(forms_list, f"{project_dir}\\{blueprint['name']}")
    with open(f"{project_dir}\\__init__.py", 'r') as f:
        init_data = f.read()
    with open(f"{project_dir}\\__init__.py", 'w') as f:
        f.write(init_data.replace('[[ blueprint_section ]]', for_main_init))

def create_run_file(project_dir, project_name):
    with open(f'{SOURCES}\\run.txt', 'r') as f:
        data = f.read()
    with open(f'{project_dir}\\run.py', 'w') as f:
        f.write(data.replace('[[ project_name ]]', project_name))

def create_forms_file(forms_list, form_file_dir):
    with open(f'{SOURCES}\\forms.txt', 'r') as f:
        data = f.read()
    all_fields = []
    all_validators = []
    for form in forms_list:
        data += f"class {form['name']}(FlaskForm):"
        for field in form['fields']:
            all_validators += field['validators']
            all_fields.append(field['type'])
            data += f"\n\t{field['name']} = {field['type']}('{field['label']}', validators = [{', '.join(field['validators'])}])"
        data += '\n\n'  
    # removing all duplicates using sets
    all_fields = set(all_fields)
    all_validators = set(all_validators)
    data = data.replace('[[ field_types ]]', ', '.join(all_fields))
    # using reg expressions to remove everything between parantheses on top of file when importing validators
    data = data.replace('[[ validators ]]', re.sub(r"\([^()]*\)", "", ', '.join(all_validators)))
    with open(f'{form_file_dir}\\forms.py', 'w') as f:
        f.write(data)

def create_init_file(req, project_dir):
    with open(f'{SOURCES}\\init.txt', 'r') as f:
        data = f.read()
    if not req['blueprints']['show']:
        data = data.replace('[[ blueprint_section ]]', f"from {req['projectName']} import routes")
    data = data.replace('[[ secret_key ]]', secrets.token_hex(16))
    # getting all necessary imports
    data = data.replace('[[ imports ]]', get_imports(req, 'init'))
    # setting up database if selected
    data = replace_placeholder(data, req['addDatabase'], '[[ db_config ]]', generate_db_config_string(req['dbType']))
    data = replace_placeholder(data, req['addAuthSys'], '[[ login_config ]]', generate_login_config_string(req['authSys']['loginView']))
    data = replace_placeholder(data, req['emails']['show'], '[[ email_config ]]', generate_email_config_string())
    with open(f"{project_dir}\\__init__.py", 'w') as f:
        f.write(data)

def create_routes_file(req, project_dir):
    data = f"from {req['projectName']} import app{get_imports(req, 'routes')}\n"
    data += "from flask import request, render_template, url_for, redirect\n"
    if req['emails']['show']:
        data += "from flask_mail import Message\n"
    # import models
    if req['addAuthSys']: 
        data += f"from {req['projectName']}.models import {req['authSys']['userTableName']}\n"
    # import forms
    if req['wtForms']['show']:
        data += f"from {req['projectName']}.forms import {', '.join([form['name'] for form in req['wtForms']['forms']])}\n"
    if req['frontend']['show'] and req['frontend']['index']:
        data += "\n@app.route('/')\n"
        data += "def index():\n\t"
        data += "return render_template('index.html')"  
    else:
        data += "\n@app.route('/')\n"
        data += "def index():\n\t"     
        data += "return '<h1>Hello World!</h1>'"
    with open(f'{project_dir}\\routes.py', 'w') as f:
        f.write(data)

def create_models_file(req, project_dir):
    if req['addAuthSys']:
        data = generate_model_string(req)
    else:
        data = ''
    with open(f'{project_dir}\\models.py', 'w') as f:
        f.write(data)

def create_frontend(frontend, project_dir, project_name):
    with open(f'{SOURCES}\\layout.txt', 'r') as f:
            data = f.read()
    with open(f'{SOURCES}\\navbar.txt', 'r') as f:
        navbar = f.read()
    
    if frontend['layout'] or frontend['index']:
        data = generate_layout_html(data, project_name, frontend, navbar)
        # saving with correct filename
        handle_index_and_layout_creation(frontend, project_dir, data)

    # creating css file
    if frontend['addCss']:
        create_css_file(frontend['addNavBar'], navbar, project_dir)
        
    # creating additional css file for checkbuttons and radiobuttons styles
    if frontend['checkRad']:
        create_checkradio_css_file(project_dir)

    # creating js file
    if frontend['addJs']:
        create_js_file(frontend['addNavBar'], project_dir, navbar)
    
    if frontend['createFormTemplates']:
        create_form_templates(frontend['layout'])
