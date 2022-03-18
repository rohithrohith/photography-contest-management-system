from cmath import log
import os
from re import sub
from importlib_metadata import email
from werkzeug.datastructures import Accept
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template,request,flash,session,jsonify,abort
from utils import *

user  = Blueprint('user',__name__,template_folder='../templates')

@user.route('/')
def Landing():
    from app import db
    import math
    cur = db.connection.cursor()
    cur.execute("""SELECT * FROM entries WHERE Type='public' LIMIT 16""")
    data = cur.fetchall()
    cur.close()
    return render_template('/pages/landing.html',data=data,iters=math.ceil(len(data)/4))

@user.route('/explore')
def Explore():
    from app import db
    import math
    if request.args:
        cur = db.connection.cursor()
        sql = """SELECT * FROM entries WHERE Type='public' AND CId IN (SELECT CId FROM tags WHERE tag REGEXP %(search)s)"""
        if cur.execute(sql,{"search":request.args['search']}):
            data = cur.fetchall()
            cur.close()
            return render_template('/pages/explore.html',data=data,iters=math.ceil(len(data)/4),nodata=False,key=request.args['search'])
        else:
            cur.close()
            return render_template('/pages/explore.html',nodata=True,key=request.args['search'])
    else:
        cur = db.connection.cursor()
        cur.execute("""SELECT * FROM entries WHERE Type='public'""")
        data = cur.fetchall()
        cur.close()
        return render_template('/pages/explore.html',data=data,iters=math.ceil(len(data)/4),nodata=False,key='')

# Contest related views
@user.route('/contests')
def Contests():
    from app import db
    cur = db.connection.cursor()
    sql = ''
    sub = {}
    key = ''
    if request.args:
        sql = """SELECT Entries,Title,ContestId,ContestType FROM contests WHERE (CloseDate>CURRENT_TIMESTAMP() AND IsOpen) AND ContestId in (SELECT CId FROM tags WHERE tag REGEXP %(key)s) ORDER BY HostedOn DESC"""
        sub["key"]= key = request.args["key"]
    else:
        sql = """SELECT Entries,Title,ContestId,ContestType FROM contests WHERE (CloseDate>CURRENT_TIMESTAMP() AND IsOpen) ORDER BY HostedOn DESC"""
    if cur.execute(sql,sub):
        data = cur.fetchall()
        return render_template('pages/contests.html',nodata=False,data=data,items=len(data),key=key)
    else:
        return render_template('pages/contests.html',nodata=True,key=key)

@user.route('/createcontest',methods=['POST','GET'])
@login_required
@verification_required
def CreateContest():
    if request.method == 'POST':
        from app import db
        import datetime
        title = request.form['title']
        contestType = request.form['contest-type']
        details = request.form['details']
        closeDate = request.form['close-date']
        tags = request.form['tags']
        formats = request.form['formats']
        id = session['uname'] + getStrTime()

        today = datetime.datetime.today()
        closeDate = datetime.datetime(int(closeDate[0:4]),int(closeDate[5:7]),int(closeDate[8:10]))
        if(today + datetime.timedelta(2)>closeDate):
            flash("Contest must be stay open for atleast 2 days","error")
            return redirect(url_for('user.CreateContest'))

        tags = tags.split(",")
        formats = formats.split(",")

        cur = db.connection.cursor()
        sql = """INSERT INTO contests (ContestId,Title,ContestType,CloseDate,Details,HostId) VALUES (%(id)s,%(title)s,%(type)s,%(date)s,%(details)s,%(host)s)"""
        substitutes = {"id":id,"title":title,"date":closeDate,"details":details,"type":contestType,"host":session['uname']}
        res = cur.execute(sql,substitutes)
        if res:
            for tag in tags:
                sql = """INSERT INTO tags (Tag,CId) VALUES (%(tag)s,%(id)s)"""  
                substitutes = {"tag":"#"+tag,"id":id}
                if not cur.execute(sql,substitutes):
                    flash("Something went wrong! please try again later","error")
                    cur.connection.close()
                    return redirect(url_for('user.CreateContest'))
            for format in formats:
                sql = """INSERT INTO formats (Format,CId) VALUES (%(format)s,%(id)s)"""  
                substitutes = {"format":"."+format,"id":id}
                if not cur.execute(sql,substitutes):
                    flash("Something went wrong! please try again later","error")
                    cur.connection.close()
                    return redirect(url_for('user.CreateContest'))
            cur.connection.commit()
            flash("Contest created!","success")
            return redirect(url_for('user.Dashboard',uname = session['uname']))
        else:
            flash("Something went wrong! please try again later","error")
            return redirect(url_for('user.CreateContest'))

    return render_template('/pages/createcontest.html')

@user.route('/contest/<string:cid>')
def Contest(cid):
    checkResource(cid)
    from app import db
    import datetime
    cur = db.connection.cursor()
    if cur.execute("""SELECT * FROM contests WHERE ContestId=%(Cid)s""",{"Cid":cid}):
        contestData = cur.fetchone()
        if cur.execute("""SELECT tag FROM tags WHERE CId=%(Cid)s""",{"Cid":cid}):
            contestTags = cur.fetchall()
            if cur.execute("""SELECT format FROM formats WHERE CId=%(Cid)s""",{"Cid":cid}):
                contestFormats = cur.fetchall()
                cdate = contestData['CloseDate']
                now = datetime.datetime.now()
                if(cdate-now > datetime.timedelta(0) and contestData['IsOpen'] == 1):
                    status = "Open"
                else:
                    status = "Closed"
                cdate = cdate.strftime("%d-%b-%Y")
                cdate=str(cdate)
                return render_template('pages/contest.html',nodata=False,contest=contestData,formats=contestFormats,tags=contestTags,status=status,cdate=cdate)
    else:
        return render_template('/pages/contest.html',nodata=True)

@user.route('/<string:cid>/entries')
@login_required
def ContestEntries(cid):
    checkResource(cid)
    from app import db
    cur = db.connection.cursor()
    if cur.execute("""SELECT e.UserId,e.EntryId,e.EntryTitle,e.EntryUrl,c.Title,c.ContestType,c.HostId,c.HasPickedWinner FROM entries e,users u,contests c WHERE CId=%(cid)s and c.HostId=u.UserName and e.CId=c.ContestId""",{"cid":cid}):
        data = cur.fetchall()
        if data[0]['ContestType'] == 'private':
            if data[0]['HostId']!=session['uname']:
                abort(403)
        return render_template('pages/entries.html',nodata=False,data=data,cname=data[0],host=data[0],cid=cid)
    else:
        cur.execute("""SELECT Title,HostId FROM contests WHERE ContestId=%(cid)s""",{"cid":cid})
        cname = cur.fetchone()
        return render_template('pages/entries.html',nodata=True,cname=cname,host=cname,cid=cid)

@user.route('/<string:cid>/winner')
def ContestWinner(cid):
    checkResource(cid)
    from app import db
    cur = db.connection.cursor()
    sql = """SELECT E.* FROM entries E,contests C,contest_winners CW WHERE CW.EntryId=E.EntryId AND CW.CId=%(cid)s"""
    subs = {"cid":cid}
    if cur.execute(sql,subs):
        data = cur.fetchone()
        return render_template('pages/winner.html',data=data)

@user.route('/<string:cid>/entryupload',methods=['POST','GET'])
@login_required
@verification_required
def Entry(cid):
    checkResource(cid)
    from app import db
    cur = db.connection.cursor()
    if request.method == "POST":
        imgTitle = request.form['file-title']
        filename = request.form['db-filename-input']
        eid = session['uname'] + "entry" + getStrTime()
        url = f'static/imageUploads/{filename}'
        substitutes = {"eid":eid,"url":url,"title":imgTitle,"cid":cid,"uid":session['uname']}
        if cur.execute("""SELECT ContestType,HostId FROM contests WHERE ContestId=%(cid)s""",substitutes):
            res = cur.fetchone()
            if res['HostId'] == session['uname']:
                flash("Contest host connot participate in his own contest!","error")
                return redirect(url_for('user.Contest',cid=cid))
            substitutes['type']=res['ContestType']
            sql = """INSERT INTO entries VALUES (%(eid)s,%(url)s,%(title)s,%(type)s,%(cid)s,%(uid)s)"""
            if cur.execute(sql,substitutes) and cur.execute("""UPDATE contests SET Entries=Entries+1 WHERE ContestId=%(cid)s""",substitutes):
                if cur.execute("""SELECT * FROM participates WHERE UserId=%(uid)s and CId=%(cid)s""",substitutes):
                    cur.connection.commit()
                    flash("Entry submitted successfully","success")
                    return redirect(url_for('user.Entry',cid=cid))
                else:
                    if not cur.execute("""INSERT INTO participates VALUES(%(uid)s,%(cid)s)""",substitutes):
                        flash("Something went wrong! please try again","error")
                        return redirect(url_for('user.Entry',cid=cid))
                cur.connection.commit()
                flash("Entry submitted successfully","success")
                return redirect(url_for('user.Entry',cid=cid))
            flash("Something went wrong! please try again","error")
            return redirect(url_for('user.Entry',cid=cid))
        else:
            flash("Something went wrong! please try again","error")
            return redirect(url_for('user.Entry',cid=cid))
    
    cur.execute("""SELECT format FROM formats WHERE CId=%(cid)s""",{"cid":cid})
    formats = cur.fetchall()
    return render_template('pages/upload.html',cid=cid,formats=formats)

@user.route('/<string:cid>/pickwinner',methods=['GET','POST'])
@login_required
@verification_required
def PickWinner(cid):
    checkPermission(cid)
    checkResource(cid)
    from app import db
    cur = db.connection.cursor()
    subs = {"id":cid}
    if cur.execute("""SELECT cw.*,EntryTitle FROM contest_winners cw,entries e WHERE cw.CId=%(id)s AND cw.CId=e.CId""",subs):
        data=cur.fetchone()
        return render_template('pages/pickwinner.html',isPicked=True,data=data)
    if request.method == "POST":
        subs['eid'] = request.form['winner']
        subs['winner'] = request.form['username']
        sql1 = """UPDATE contests SET HasPickedWinner=true,IsOpen=false WHERE ContestId=%(id)s"""
        sql2 = """INSERT INTO contest_winners(WinnerId,CId,EntryId) VALUES (%(winner)s,%(id)s,%(eid)s)"""
        if cur.execute(sql1,subs) and cur.execute(sql2,subs):
            db.connection.commit()
            flash("Winner chosen!","success")
            return redirect(url_for('user.Dashboard',uname=session['uname']))
        else:
            flash("Something went wrong please try again!","error")
            return redirect(url_for('user.PickWinner',cid=cid))
    else:
        sql = """SELECT * FROM entries WHERE CId=%(id)s"""
        if cur.execute(sql,subs):
            data = cur.fetchall()
            return render_template('pages/pickwinner.html',entries=data,nodata=False,ispicked=False)
        else:
            return render_template('pages/pickwinner.html',nodata=True,ispicked=False)

# User views
@user.route('/dashboard/<string:uname>')
@login_required
def Dashboard(uname):
    if not uname == session["uname"]:
        abort(401)
    hcontests = []
    pcontests = []
    hnodata = False
    pnodata = False
    from app import db
    cur = db.connection.cursor()
    if cur.execute("""SELECT UserName,IsVerified,MailId FROM users WHERE UserName=%(id)s""",{"id":uname}):
        data=cur.fetchone()
        sql = """SELECT * FROM contests WHERE ContestId IN (SELECT CId from participates WHERE UserId=%(uid)s)"""
        subs = {"uid":uname}
        if cur.execute(sql,subs):
            pcontests = cur.fetchall()
            pnodata = False
        else:
            pnodata = True
        
        sql = """SELECT * FROM contests WHERE HostId=%(uid)s"""
        if cur.execute(sql,subs):
            hnodata = False
            hcontests=cur.fetchall()
        else:
            hnodata=True

        return render_template('/pages/dashboard.html',data=data,pcontests=pcontests,hcontests=hcontests,hnodata=hnodata,pnodata=pnodata)
    else:
        flash("Something went try again later","error")
        return redirect(url_for('user.Dashborad',uname=uname))

@user.route('/<string:uname>/collections')
@login_required
def Collections(uname):
    if not uname == session["uname"]:
        abort(401)
    from app import db
    import math
    cur = db.connection.cursor()
    sql = """SELECT E.*,UC.* FROM user_collections UC,entries E WHERE UC.UserId = %(uid)s AND UC.EntryId=E.EntryId"""
    subs = {"uid":session['uname']}
    data=None
    if cur.execute(sql,subs):
        data = cur.fetchall()
        return render_template('pages/usercollections.html',nodata=False,data=data,len=len(data),iters=math.ceil(len(data)/4))
    else:
        return render_template('pages/usercollections.html',nodata=True)
        
@user.route('/addtocollection/<string:eid>')
@login_required
@verification_required
def AddToCollections(eid):
    from app import db
    cur = db.connection.cursor()
    subs = {"eid":eid,"uid":session['uname']}
    sql = """SELECT * FROM user_collections WHERE EntryId=%(eid)s AND UserId=%(uid)s"""
    if cur.execute(sql,subs):
        flash("Item already in your collection!","error")
    else:
        sql = """INSERT INTO user_collections VALUES(%(eid)s,%(uid)s)"""
        if cur.execute(sql,subs):
            db.connection.commit()
            flash("Image added to your collection!","success")
        else:
            flash("Something went wrong! try again later","error")
    return redirect(url_for('user.Collections',uname=session['uname']))

@user.route('/<string:uid>/changepassword',methods=['POST'])
def ChangePassword(uid):
    if not uid == session["uname"]:
        abort(401)
    if request.method=="POST":
        from app import db,bcrypt
        currentPassword = request.form['current-password']
        newPassword = request.form['new-password']
        cNewPassword = request.form['confirm-new-password']
        if not newPassword == cNewPassword:
            flash("New passwords doesn't match!","error")
            return redirect(url_for('user.Dashboard',uname=uid))
        else:
            cur = db.connection.cursor()
            cur.execute("""SELECT Password FROM users WHERE UserName=%(uid)s""",{"uid":uid})
            oldPassword = cur.fetchone()['Password']
            if bcrypt.check_password_hash(oldPassword,currentPassword):
                sql = """UPDATE users SET Password=%(npw)s WHERE UserName=%(uid)s"""
                subs = {"npw":bcrypt.generate_password_hash(newPassword),"uid":uid}
                if cur.execute(sql,subs):
                    flash("Password changed successfully!","success")
                    db.connection.commit()
                    return redirect(url_for('user.Dashboard',uname=uid))
                else:
                    flash("Something went wrong try again later!","error")
                    return redirect(url_for('user.Dashboard',uname=uid))
            flash("Wrong current password!","error")
            return redirect(url_for('user.Dashboard',uname=uid))

@user.route('/verifyaccount/<string:uname>')
@login_required
def VerifyAccount(uname):
    if not uname == session["uname"]:
        abort(401)
    from app import db
    cur = db.connection.cursor()
    if cur.execute("""UPDATE users SET IsVerified = TRUE WHERE UserName = %(uid)s""",{"uid":uname}):
        db.connection.commit()
        session['isVerified'] = 1
        flash("Acccount verified","success")
    else:
        flash("Something went wrong! please try again later","error")
    return redirect(url_for('user.Dashboard',uname=uname))

@user.route('/forgotpassword',methods=['POST'])
def ForgotPassword():
    from app import db,bcrypt
    cur = db.connection.cursor()
    password = request.form['password']
    cpassword = request.form['confirm-password']
    mailId = request.form['email']
    otp = request.form['forgot-otp']

    if session['otp'] != otp:
        flash("Wrong OTP","error")
        return redirect(url_for('auth.Signin'))

    if password != cpassword:
        flash("Passwords doesn't match","error")
        return redirect(url_for('auth.Signin'))
    
    if cur.execute("""UPDATE users SET Password=%(pass)s WHERE MailId=%(mail)s""",{"pass":bcrypt.generate_password_hash(password),"mail":mailId}):
        db.connection.commit()
        session.pop('otp')
        flash("Password changed!",'success')
        return redirect(url_for('auth.Signin'))
    else:
        flash("Something went wrong! try again later!",'error')
        return redirect(url_for('auth.Signin'))


#  REQUESTS

@user.route('/uploadimage/<string:cid>',methods=['POST'])
@login_required
def UploadImage(cid):
    from app import db
    extentions = []
    data = None
    cur = db.connection.cursor()
    if cur.execute("""SELECT format FROM formats WHERE CId=%(cid)s""",{"cid":cid}):
        data = cur.fetchall()
        file = request.files['file']
        for format in data:
            extentions.append(format['format'].lower())
        fileExtention = os.path.splitext(file.filename)[1]
        if fileExtention.lower() in extentions:
            file.filename = session['uname']+getStrTime()+file.filename
            fileName = secure_filename(file.filename)
            file.save(os.path.join('static/imageUploads/',fileName))
            return fileName
        else:
            return "-1"
    else:
        return "0"

@user.route('/deleteimage',methods=['GET'])
@login_required
def DeleteImage():
    data = request.args.get('file')
    data = data
    try:
        os.remove(f'static/imageUploads/{data}')
        return "True"
    except:
        return "False"

@user.route('/getotp',methods=['POST'])
def GetOtp():
    from app import db
    cur = db.connection.cursor()
    data = request.data.decode("utf-8")
    if cur.execute("""SELECT * FROM users WHERE MailId=%(mail)s""",{"mail":data}):
        otp = generateOtp()
        print(otp)
        session['otp'] = otp
        return data
    else:
        return str(False)

@user.route('/contestsfilter')
def filterContests():
    from app import db
    cur = db.connection.cursor()
    sql = ''
    sub = {}
    sub['key'] = ''
    sub["type"] = request.args['filter']
    if 'key' in request.args:
        sub["key"] = request.args["key"]
        sql = """SELECT Title,ContestId,ContestType,Entries FROM contests WHERE (CloseDate>CURRENT_TIMESTAMP() AND IsOpen) AND ContestType=%(type)s AND ContestId in (SELECT CId FROM tags WHERE tag REGEXP %(key)s)"""
    else:
        sql = """SELECT Title,ContestType,ContestId,Entries from contests WHERE (CloseDate>CURRENT_TIMESTAMP() AND IsOpen) AND ContestType=%(type)s"""
    if cur.execute(sql,sub):
        data = cur.fetchall()
        return jsonify(data)
    else:
        return "no data"