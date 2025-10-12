from flask import Blueprint

media_blue = Blueprint('media', __name__)

from . import views
from . import model
