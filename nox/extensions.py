import celery
from flask_appbuilder import AppBuilder
from flask_appbuilder.security.mongoengine.manager import SecurityManager
from flask_mongoengine import MongoEngine
from flask_migrate import Migrate

APP_DIR = os.path.dirname(__file__)

celery_app = celery.Celery()
db = MongoEngine()
