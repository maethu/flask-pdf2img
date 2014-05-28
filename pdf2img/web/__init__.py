from flask import Flask
from flask import make_response
from flask import request
from flask.ext.cache import Cache
from pdf2img import Pdf2Img
from tempfile import NamedTemporaryFile
import os

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

converter = Pdf2Img()


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

if __name__ == "__main__":
    app.run(debug=True)
