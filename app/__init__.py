import os

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_admin import Admin
from flask_sslify import SSLify

app = Flask(__name__)

app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)

if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
    sslify = SSLify(app)

from app import routes, models, admin as adm

admin = Admin(
    app,
    name='Reading List',
    index_view=adm.RLModelView(models.User, db.session, endpoint='admin',
                               url='/admin'),
    template_mode='bootstrap3',
    base_template='my_master.html'
)
admin.add_view(adm.RLModelView(models.Book, db.session))
