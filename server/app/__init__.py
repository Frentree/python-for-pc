import json

from flask import Flask, request, jsonify
from app.database.maria import *

print("init")
print(__name__)

app = Flask(__name__)
app.jinja_env.auto_reload = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

from app.controllers.service_controller import *

