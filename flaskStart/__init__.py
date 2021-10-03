from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'       # use environment var in production

SOURCES = f"{app.root_path}\\static\\sources"
BASE_TEMPLATE = "{% extends \"layout.html\" %}\n\n{% block content %}\n\n{% endblock content %}"

from flaskStart import routes