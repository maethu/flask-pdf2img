from flask import Flask
from flask import make_response
from flask import redirect
from flask import request
from flask import url_for
from flask.ext import login
from flask.ext.admin import Admin
from flask.ext.admin import AdminIndexView
from flask.ext.admin import expose
from flask.ext.admin import helpers
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy
from pdf2img import Pdf2Img
from tempfile import NamedTemporaryFile
from wtforms import fields
from wtforms import form
from wtforms import validators
import os


app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

app.config['DATABASE_FILE'] = 'db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{0}'.format(
    app.config['DATABASE_FILE'])
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

converter = Pdf2Img()


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


class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(User).filter_by(login=self.login.data).first()


class AdminLoginView(AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated():
            return redirect(url_for('.login_view'))
        return super(AdminLoginView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated():
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(AdminLoginView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))

admin = Admin(app,
              name="Pdf2Img",
              index_view=AdminLoginView(),
              base_template='admin_main.html')


class AuthModelView(ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated()

admin.add_view(AuthModelView(ApiKeys, db.session))


@app.route('/')
def index():
    return "This is the pdf2img service... stay tuned"


@app.route('/input', methods=['GET', 'POST'])
def input():

    files = request.files
    if len(files) != 1:
        return 'BADREQUEST'

    # get file
    file_ = files.values()[0]

    # tmp store the file
    tmpfile = NamedTemporaryFile(delete=False)
    tmp_filename = tmpfile.name
    tmpfile.write(file_.read())
    tmpfile.close()
    result = converter.convert(tmpfile.name)

    os.remove(tmp_filename)

    return str(result)


@app.route('/expose/<folderhash>/<image_name>')
@cache.cached(timeout=300)
def expose(folderhash, image_name):
    path = "{0}/{1}/{2}".format(converter.path, folderhash, image_name)

    handler = open(path, 'r')
    response = make_response(handler.read())
    response.content_type = "image/png"

    handler.close()
    return response


def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)

init_login()


def init_db():
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        db.create_all()
        admin = User(login="admin", password="admin")
        db.session.add(admin)
        db.session.commit()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
