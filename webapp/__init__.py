from flask import Flask
from flask import make_response
from flask import request
from flask.ext import login
from flask.ext.admin import Admin
from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy
from pdf2img import Pdf2Img
from tempfile import NamedTemporaryFile
import os


app = Flask(__name__)
converter = Pdf2Img()

# App config
# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

app.config['DATABASE_FILE'] = 'db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{0}'.format(
    app.config['DATABASE_FILE'])
app.config['SQLALCHEMY_ECHO'] = True

# Database
db = SQLAlchemy(app)
from webapp.models import ApiKeys
from webapp.models import User


cache = Cache(app, config={'CACHE_TYPE': 'simple'})


# Admin interface
from webapp.admin import AdminLoginView
from webapp.admin import AuthModelView

admin = Admin(app,
              name="Pdf2Img",
              index_view=AdminLoginView(),
              base_template='admin_main.html')

admin.add_view(AuthModelView(ApiKeys, db.session))
admin.add_view(AuthModelView(User, db.session))


@app.route('/')
def index():
    return "This is the pdf2img service... stay tuned"


def check_apikey_domain(domain, apikey):
    # XXX replace domain  localhost
    record = ApiKeys.query.filter_by(domain='localhost').first()

    if not record:
        return False
    return record.apikey == apikey


@app.route('/input', methods=['POST'])
def input():

    apikey = request.form.get('apikey')
    domain = ''
#    domain = request... XXX get domain

    if not check_apikey_domain(domain, apikey):
        return 'BADREQUEST'

    file_ = request.files.get('file')
    if file_ is None:
        return 'BADREQUEST'

    # tmp store the file
    tmpfile = NamedTemporaryFile(delete=False)
    tmp_filename = tmpfile.name
    tmpfile.write(file_.read())
    tmpfile.close()
    result = converter.convert(tmpfile.name)

    os.remove(tmp_filename)

    return str(result)


@app.route('/expose/<folderhash>/<image_name>', methods=['GET'])
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
        apikey = ApiKeys(domain='localhost', apikey='12345')

        db.session.add(admin)
        db.session.add(apikey)
        db.session.commit()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
