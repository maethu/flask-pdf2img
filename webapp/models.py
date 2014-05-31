from webapp import db
from werkzeug.security import generate_password_hash


class ApiKeys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(120), unique=True)
    apikey = db.Column(db.String(120), unique=True)

    def __repr__(self):
        return '<APIKey for {0}>' % self.domain

    def __unicode__(self):
        return self.domain


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(120))
    password = db.Column(db.String(64))

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.password = generate_password_hash(self.password)

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.login

    def __repr__(self):
        return '<User for {0}>' % self.login
