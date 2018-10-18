from time import time
from datetime import datetime
import jwt
from app import app, db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    books = db.relationship('Book', backref='reader', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.Column(db.String(150))
    edition = db.Column(db.SmallInteger)
    format = db.Column(db.SmallInteger)
    about = db.Column(db.String(500))
    isbn = db.Column(db.String(20))   # isbn length may increase in
                                      # future.
    private = db.Column(db.Boolean)
    list = db.Column(db.SmallInteger, index=True, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Book {}>'.format(self.title)
