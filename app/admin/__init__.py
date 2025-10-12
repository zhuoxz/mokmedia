from flask import Blueprint

admin_blue = Blueprint('admin', __name__)

from . import controller
from . import model
from . import views
