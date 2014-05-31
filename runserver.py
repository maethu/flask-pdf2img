from webapp import app
from webapp import init_db

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
