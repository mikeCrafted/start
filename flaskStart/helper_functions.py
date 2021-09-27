from flaskStart import SOURCES

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

def get_navbar_substring(navbar, section):
    return navbar[navbar.index(section) + len(section) : navbar.index(section.replace('start', 'end'))]

def handle_index_and_layout_creation(frontend, project_dir, data):
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

def create_js_file(add_navbar, project_dir, navbar):
    js = ''
    if add_navbar:
        js = get_navbar_substring(navbar, '[[ navbar_js_start ]]')
    with open(f"{project_dir}\\static\\main.js", 'w') as f:
        f.write(js)

def create_checkradio_css_file(project_dir):
    with open(f'{SOURCES}\\checkRad.txt', 'r') as f:
        check_rad_css = f.read()
    with open(f"{project_dir}\\static\\checkradio.css", 'w') as f:
        f.write(check_rad_css)

def create_css_file(add_navbar, navbar, project_dir):
    with open(f'{SOURCES}\\mainCss.txt', 'r') as f:
        css = f.read()
    css = replace_placeholder(css, add_navbar, '[[ nav ]]', get_navbar_substring(navbar, '[[ navbar_css_start ]]'), placeholder_if_false = '[[ nav ]]\n\n')
    css = replace_placeholder(css, add_navbar, '[[ navbar_css_mobile ]]', get_navbar_substring(navbar, '[[ navbar_css_mobile_start ]]'), placeholder_if_false = '[[ navbar_css_mobile ]]')
    css = replace_placeholder(css, add_navbar, '[[ navbar_css_animation ]]', get_navbar_substring(navbar, '[[ navbar_css_animation_start ]]'), placeholder_if_false = '[[ navbar_css_animation ]]')
    with open(f"{project_dir}\\static\\main.css", 'w') as f:
        f.write(css)

def generate_layout_html(data, project_name, frontend, navbar):
    data = data.replace('[[ project_name ]]', project_name)
    data = replace_placeholder(data, frontend['addCss'], '[[ main_css_link ]]', create_css_link('main.css'), placeholder_if_false = '[[ main_css_link ]]\n        ')
    data = replace_placeholder(data, frontend['checkRad'], '[[ radio_check_css_link ]]', create_css_link('checkradio.css'), placeholder_if_false = '[[ radio_check_css_link ]]\n        ')
    data = replace_placeholder(data, frontend['addNavBar'], '[[ nav ]]', get_navbar_substring(navbar, '[[ navbar_html_start ]]'))
    scripts_link = f"<script src=\"{{{{ url_for('static', filename = 'main.js') }}}}\"></script>"
    data = replace_placeholder(data, frontend['addJs'], '[[ scripts ]]', scripts_link, placeholder_if_false = '[[ scripts ]]')
    return data

def create_form_templates(use_layout):
    pass

