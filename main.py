from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail, Message
import json
import os
import math

with open("config.json", "r") as c:
    params = json.load(c)["params"]
local_server = True

app = Flask(__name__)
app.secret_key = "shuvos-secret-17"
app.config["UPLOAD_FOLDER"] = params["upload_location"]
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT="465",
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["gmail-user"],
    MAIL_PASSWORD=params["gmail-password"]
)
mail = Mail(app)

if (local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)


class Contacts(db.Model):
    """
    id, name, email, ph_num, msg, date
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    ph_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

    # def __repr__(self):
    # return '<User %r>' % self.username


class Post(db.Model):
    """
    id, title, slug, contacts, date, img_file
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Post.query.filter_by().all()
    last = math.ceil(len(posts)/int(params["no_of_posts"]))
    page = request.args.get("page")
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params["no_of_posts"]): (page-1)*int(params["no_of_posts"])+int(params["no_of_posts"])]
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif (page==last):
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page=" + str(page+1)
    return render_template("home.html", params=params, posts=posts, prev=prev, next=next)


@app.route("/post/<string:post_slug>", methods=["GET"])
def post_route(post_slug):
    post = Post.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, post=post)

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():

    if "user" in session and session["user"] == params["admin_name"]:
        posts = Post.query.filter_by().all()
        return render_template("dashboard.html", params=params,posts=posts)

    if request.method=="POST":
        username = request.form.get("uname")
        userpassword = request.form.get("upassword")
        if username == params["admin_name"] and userpassword == params["admin_password"]:
            # set the session variable
            session["user"] = username
            posts = Post.query.filter_by().all()
            return render_template("dashboard.html", params=params,posts=posts)
    else:
        return render_template("signin.html", params=params)

@app.route("/edit/<string:id>", methods=["GET", "POST"])
def edit(id):
    if ("user" in session and session["user"] == params["admin_name"]):
        if request.method=="POST":
            title = request.form.get("title")
            tline = request.form.get("tline")
            slug = request.form.get("slug")
            content = request.form.get("content")
            img_file = request.form.get("img_file")
            date = datetime.now()
            if id == "0":
                posts = Post(title=title, tagline=tline, slug= slug, content=content, img_file=img_file, date=date)
                db.session.add(posts)
                db.session.commit()
            else:
                posts = Post.query.filter_by(id=id).first()
                posts.title = title
                posts.tline = tline
                posts.slug = slug
                posts.content = content
                posts.img_file = img_file
                posts.date = date
                db.session.commit()
                return redirect("/edit/" + id)
        posts = Post.query.filter_by(id=id).first()
        return render_template("edit.html", params=params, posts=posts, id=id)

@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if "user" in session and session["user"]==params["admin_name"]:
        if request.method == "POST":
            f = request.files["file"]
            f.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f.filename)))
            return "File uploaded successfully! "

@ app.route('/logout')
def logout():
    session.pop("user")
    return redirect("/dashboard")

@app.route("/delete/<string:id>", methods=["GET", "POST"])
def delete(id=id):
    if "user" in session and session["user"] == params["admin_name"]:
        posts = Post.query.filter_by(id=id).first()
        db.session.delete(posts)
        db.session.commit()
        return redirect("/dashboard")


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if (request.method == "POST"):
        """Add entry to the database"""
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        message = request.form.get("message")
        entry = Contacts(name=name, email=email, ph_num=phone,
                         msg=message, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("new message from" + name,
                          sender=email,
                          recipients=[params["gmail-user"]],
                          body=message + "\n PH_num: " + phone
                          )

    return render_template("contact.html", params=params)


if __name__ == "__main__":
    app.run(debug=True, port=3000)
