from flask import Blueprint

api_blue = Blueprint('api', __name__)

from . import views
from . import controller



