from pdf2img.web import app
from pdf2img.web import init_db

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
