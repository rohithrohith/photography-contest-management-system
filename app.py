from flask import Flask, render_template,redirect,abort,Blueprint,flash,session,url_for
from flask_mysqldb import MySQL
from blueprints.auth import auth
from blueprints.user import user
from config import DevConfig
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import HTTPException

app = Flask(__name__)
app.config.from_object(DevConfig)
db = MySQL()
db.init_app(app)
bcrypt = Bcrypt(app)

app.register_blueprint(auth)
app.register_blueprint(user)

@app.errorhandler(HTTPException)
def error_handler(e):
    return render_template('error-pages/error.html',e=e)


if __name__ == "__main__":
    app.run(debug=True,port=5500)
