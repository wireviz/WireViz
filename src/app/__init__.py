from flask import Flask, Blueprint
from flask_restplus import Api

app = Flask(__name__)
blueprint = Blueprint('api', __name__, url_prefix='')
api = Api(blueprint, doc='/doc/', version='1.0', title='WireViz server',
    description='WireViz is a tool for easily documenting cables, wiring harnesses and connector pinouts. It takes plain text, YAML-formatted files as input and produces beautiful graphical output (SVG, PNG, ...) thanks to GraphViz. It handles automatic BOM (Bill of Materials) creation and has a lot of extra features.',)
app.register_blueprint(blueprint)
# app.config.from_object('config')
from app import server