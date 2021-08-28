import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()

DB_NAME = "database.db"


def create_app(test_config=None):
    """Application factory model: create and configure app, return app."""
    # name of enclosing module passed to create app
    app = Flask(__name__)
    # random secret key
    app.config['SECRET_KEY'] = "dev"

    # this for remote:
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/www/aws_flask/flask1/website/database/test2.db'

    # these for local:
    file_path = os.path.abspath(os.getcwd()) + "\test2.db"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+file_path

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from .views import views
    from .auth import auth
    from .models import User

    db.init_app(app)

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    
    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def create_database(app):
    # if not path.exists('website/' + DB_NAME):

    db.create_all(app=app)
    print('Created database')




