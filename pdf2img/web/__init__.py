from flask import Flask
from flask import make_response
from flask import request
from flask.ext.admin import Admin
from flask.ext.admin import expose
from flask.ext.admin.contrib.sqla import ModelView
from flask.ext.cache import Cache
from flask.ext.sqlalchemy import SQLAlchemy
from pdf2img import Pdf2Img
from tempfile import NamedTemporaryFile
import os


app = Flask(__name__)

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


admin = Admin(app, name="Pdf2Img")
# admin.add_view(ApiKEey(name='API keys'))
admin.add_view(ModelView(ApiKeys, db.session))


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


def init_db():
    # Build a sample db on the fly, if one does not exist yet.
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        db.create_all()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
