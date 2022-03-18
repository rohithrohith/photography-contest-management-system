from flask import Blueprint, render_template, abort,request,flash,url_for,session
from werkzeug.utils import redirect

auth  = Blueprint('auth',__name__,template_folder='../templates')

@auth.route('/signin',methods=['POST','GET'])
def Signin():
    session.clear()
    if request.method == "POST":
        signinId = request.form['email-or-username']
        password = request.form['password']

        from app import bcrypt,db

        cur = db.connection.cursor()
        sql = """SELECT * FROM users WHERE UserName=%(uname)s OR MailId= %(mail)s"""
        data = {"uname":signinId,"mail":signinId}
        res = cur.execute(sql, data)
        if res == 1:
            data = cur.fetchone()
            if bcrypt.check_password_hash(data['Password'], password):
                session['isLogedIn'] = True
                session['uname'] = data['UserName']
                session['isVerified'] = data['IsVerified']
                flash("Login success","success")
                return redirect(url_for('user.Landing'))
            else:
                flash("Wrong password!","error")
                return render_template("/pages/signin.html")
        else:
            flash("Account doesn't exists! register now","error")

    return render_template("/pages/signin.html")   

@auth.route('/register',methods=['POST','GET'])
def Register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cpassword = request.form['confirm-password']

        from app import db,bcrypt
        if cpassword != password:
            flash("Passwords does not match!","error")
            return render_template("/pages/register.html")
        cur = db.connection.cursor()
        cur.execute("""SELECT * FROM users WHERE MailId=%(mail)s""", {"mail":email})
        res = cur.fetchone()
        if res:
            flash("User already exists! try signing in","error")
            return redirect(url_for('auth.Signin'))
        else:
            cur.execute("SELECT * FROM users WHERE UserName=%(uname)s",{"uname":username})
            if cur.fetchone():
                flash("Username already exists! try different one","error")
            else:
                if cur.execute("INSERT INTO users (UserName,MailId,Password) VALUES (%(uname)s,%(mail)s,%(pass)s)",{"uname":username,"mail":email,"pass":bcrypt.generate_password_hash(password)}):
                    cur.connection.commit()
                    cur.close()
                    flash("User registration success!","success")
                    return redirect(url_for('auth.Signin'))
                else:
                    flash("Something went wrong! please try again later","error")
        return render_template("/pages/register.html")

    return render_template("/pages/register.html")

@auth.route('/logout')
def Logout():
    session.clear()
    flash("Logout successful","success")
    return redirect(url_for('user.Landing'))