from flask import redirect,session,flash,url_for,session,abort
import datetime
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'isLogedIn' not in session:
            flash("Your session ended please signin again!","error")
            return redirect(url_for('auth.Signin'))
        return f(*args, **kwargs)
    return decorated_function

def verification_required(f):
    @wraps(f)
    def decorated_function2(*args,**kwargs):
        from app import db
        cur = db.connection.cursor()
        if cur.execute("""SELECT IsVerified FROM users WHERE UserName=%(uid)s""",{"uid":session['uname']}):
            res = cur.fetchone()
            if res['IsVerified'] == 0:
                flash("Please verify your account to access the page!","error")
                return redirect(url_for('user.Dashboard',uname=session['uname']))
            return f(*args,**kwargs)
    return decorated_function2

def getStrTime():
    nowTime = datetime.datetime.now()
    nowTime= str(nowTime.timestamp())
    nowTime = nowTime.replace(".","")
    return str(nowTime)

def checkPermission(cid):
    from app import db
    cur = db.connection.cursor()
    if cur.execute("""SELECT HostId FROM contests WHERE ContestId=%(cid)s""",{"cid":cid}):
        if not cur.fetchone()['HostId'] == session['uname']:
            abort(401)

def generateOtp() :
    import random,math
    digits = "0123456789"
    OTP = ""
    for i in range(6) :
        OTP += digits[math.floor(random.random() * 10)]
    return OTP

def checkResource(cid):
    from app import db
    cur = db.connection.cursor()
    if not cur.execute("""SELECT HostId FROM contests WHERE ContestId=%(cid)s""",{"cid":cid}):
        abort(404)