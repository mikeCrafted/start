from flask import render_template, request, make_response, jsonify
from flaskStart import app, SOURCES
from venv import EnvBuilder
import secrets, os, re


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

# helper function to return all imports needed for __init__ or routes file based on user selection
def get_imports(req, destination):
    imports = ""
    if req['addDatabase']:
        if destination == 'init':
            imports += "from flask_sqlalchemy import SQLAlchemy\n"
        else:
            imports += ', db'
    if req['addAuthSys']:
        if destination == 'init':
            imports += "from flask_bcrypt import Bcrypt\n"
            imports += "from flask_login import LoginManager\n"
        else:
            imports += ', bcrypt'
    if req['emails']['show']:
        if destination == 'init':
            imports += "from flask_mail import Mail"
        else:
            imports += ', mail'
    return imports

def create_models_file(req, project_dir):
    if req['addAuthSys']:
        data = generate_model_string(req)
    else:
        data = ''
    with open(f'{project_dir}\\models.py', 'w') as f:
        f.write(data)

def create_frontend(frontend, project_dir, project_name):
    if frontend['layout'] or frontend['index']:
        with open(f'{SOURCES}\\layout.txt', 'r') as f:
            data = f.read()
        data = data.replace('[[ project_name ]]', project_name)
        data = replace_placeholder(data, frontend['addCss'], '[[ main_css_link ]]', create_css_link('main.css'), placeholder_if_false = '[[ main_css_link ]]\n        ')
        data = replace_placeholder(data, frontend['checkRad'], '[[ radio_check_css_link ]]', create_css_link('checkradio.css'), placeholder_if_false = '[[ radio_check_css_link ]]\n        ')
        data = replace_placeholder(data, frontend['addNavBar'], '[[ nav ]]', read_navbar_html_string())
        scripts_link = f"<script src=\"{{{{ url_for('static', filename = 'main.js') }}}}\"></script>"
        data = replace_placeholder(data, frontend['addJs'], '[[ scripts ]]', scripts_link, placeholder_if_false = '[[ scripts ]]')

        # saving with correct filename
        if frontend['layout'] and frontend['index']:
            with open(f"{project_dir}\\templates\\layout.html", 'w') as f:
                f.write(data)
            with open(f"{project_dir}\\templates\\index.html", 'w') as f:
                f.write("{% extends \"layout.html\" %}\n\n{% block content %}\n\n{% endblock content %}")
        elif frontend['layout']:
            with open(f"{project_dir}\\templates\\layout.html", 'w') as f:
                f.write(data)
        elif frontend['index']:
            with open(f"{project_dir}\\templates\\index.html", 'w') as f:
                f.write(data)

    # creating css file
    if frontend['addCss']:
        with open(f'{SOURCES}\\mainCss.txt', 'r') as f:
            css = f.read()

        if frontend['addNavBar']:
            with open(f'{SOURCES}\\navbar.txt', 'r') as f:
                navbar = f.read()
            css = css.replace('[[ nav ]]', navbar[navbar.index('[[ navbar_css_start ]]') + 22 : navbar.index('[[ navbar_css_end ]]')])
            css = css.replace('[[ navbar_css_mobile ]]', navbar[navbar.index('[[ navbar_css_mobile_start ]]') + 29 : navbar.index('[[ navbar_css_mobile_end ]]')])
            css = css.replace('[[ navbar_css_animation ]]', navbar[navbar.index('[[ navbar_css_animation_start ]]') + 32 : navbar.index('[[ navbar_css_animation_end ]]')])
        else:
            css = css.replace('[[ nav ]]\n\n', '')
            css = css.replace('[[ navbar_css_mobile ]]', '')
            css = css.replace('[[ navbar_css_animation ]]', '')
        with open(f"{project_dir}\\static\\main.css", 'w') as f:
            f.write(css)
    
    # creating additional css file for checkbuttons and radiobuttons styles
    if frontend['checkRad']:
        with open(f'{SOURCES}\\checkRad.txt', 'r') as f:
            check_rad_css = f.read()
        with open(f"{project_dir}\\static\\checkradio.css", 'w') as f:
            f.write(check_rad_css)

    # creating js file
    if frontend['addJs']:
        js = ''
        if frontend['addNavBar']:
            with open(f'{SOURCES}\\navbar.txt', 'r') as f:
                navbar = f.read()
            js = navbar[navbar.index('[[ navbar_js_start ]]') + 21 : navbar.index('[[ navbar_js_end ]]')]
        with open(f"{project_dir}\\static\\main.js", 'w') as f:
            f.write(js)
    

def create_css_link(filename):
    return f"<link rel=\"stylesheet\" type=\"text/css\" href=\"{{{{ url_for('static', filename = '{filename}') }}}}\">"


def generate_db_config_string(db_type):
    if db_type == 'MySQL':
        db_config = "app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/site'\n"
    else:
        db_config = "app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'\n"
    db_config += "db = SQLAlchemy(app)\n"
    db_config += "db.create_all()\n"
    db_config += "db.session.commit()\n\n"
    return db_config

def generate_login_config_string(login_view):
    login_config = "bcrypt = Bcrypt(app)\n"
    # setting up loginManager
    login_config += "login_manager = LoginManager(app)\n"
    login_config += f"login_manager.login_view = '{login_view}'\n"
    login_config += "login_manager.login_message_category = 'info'\n\n"
    return login_config

def generate_email_config_string():
    email_config  = "app.config['MAIL_SERVER'] = ''          # for example 'smtp.gmail.com'\n"
    email_config += "app.config['MAIL_PORT'] = ''            # for example 587\n"
    email_config += "app.config['MAIL_USE_TLS'] = True\n"
    email_config += "app.config['MAIL_USERNAME'] = ''        # your mail username\n"
    email_config += "app.config['MAIL_PASSWORD'] = ''        # Don't set your password here as string, use environment variables\n"
    email_config += "mail = Mail(app)\n\n"
    return email_config

def generate_blueprint_imports_string(project_name, blueprint_name):
    data = f"from {project_name} import app\n" 
    data += "from flask import Blueprint, render_template, url_for, redirect, request\n\n"
    data += f"{blueprint_name} = Blueprint('{blueprint_name}', __name__)\n"
    data += f"# Use @{blueprint_name}.route()"
    return data

def replace_placeholder(data, condition, placeholder, new_value, placeholder_if_false = ""):
    if condition:
        data = data.replace(placeholder, new_value)
    else:
        if placeholder_if_false == "":
            data = data.replace(f"{placeholder}\n", '')
        else:
            data = data.replace(placeholder_if_false, '')
    return data

def generate_model_string(req):
    data = f"from {req['projectName']} import db, login_manager\n"
    data += "from flask_login import UserMixin\n\n"
    data += "@login_manager.user_loader\n"
    data += "def load_user(user_id):\n\t"
    data += f"return {req['authSys']['userTableName']}.query.get(int(user_id))\n\n"
    data += f"class {req['authSys']['userTableName']}(db.Model, UserMixin):\n"
    for field in req['authSys']['userTableFields']:
        data += f"\t{field['name']} = db.Column(db.{field['type']}, primary_key = {field['pk']}, nullable = {field['nullable']}, unique = {field['unique']})\n"
    return data

def read_navbar_html_string():
    with open(f'{SOURCES}\\navbar.txt', 'r') as f:
        navbar = f.read()
    return navbar[navbar.index('[[ navbar_html_start ]]') + 23 : navbar.index('[[ navbar_html_end ]]')]

