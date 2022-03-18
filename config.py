from os import environ, path
from dotenv import load_dotenv

baseDir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(baseDir,'.env'))

class Config:
    SECRET_KEY = environ.get('SECRET_KEY')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'


class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False


class DevConfig(Config):
    MYSQL_HOST=environ.get('dbhost')
    MYSQL_USER=environ.get('dbuser')
    MYSQL_PASSWORD=environ.get('dbpass')
    MYSQL_DB=environ.get('dbname')
    DEBUG = True
    TESTING = True
    MYSQL_CURSORCLASS = 'DictCursor'