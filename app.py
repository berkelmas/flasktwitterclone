import locale
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from flask_uploads import IMAGES, UploadSet, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import BooleanField, PasswordField, StringField, TextAreaField
from wtforms.validators import InputRequired, Length

photos= UploadSet('photos', IMAGES)

locale.setlocale(locale.LC_TIME, "tr_TR")

app= Flask(__name__)

app.config['UPLOADED_PHOTOS_DEST']= 'images'

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///engage.db"
app.config['DEBUG']= True
app.config['SECRET_KEY'] = 'burasicokgizli!!!'



configure_uploads(app, photos)

login_manager = LoginManager(app)
login_manager.login_view= 'login'      ## bu kodumuz ile; kullanici giris yapmadigi durumlarda, eger ki giris yapilmasi gereken bir sayfaya gitmek isterse, onu profile isimli fonksiyonumuzun url ine yonlendiriyoruz.

login_manager.login_message = 'Bu sayfaya ulaşmak için lütfen giriş yapınız.'
login_manager.login_message_category = "danger"

db = SQLAlchemy(app)
migrate= Migrate(app, db)

manager= Manager(app)
manager.add_command('db', MigrateCommand)

follower = db.Table('follower',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),         ## Bunu direk olarak kullanamayacagimiz -aslinda sqlalchemy'nin kendi basina bu tabloyu kullanacagi icin, bu tabloyu model olarak degil; direk tablo olarak olusturuyoruz.
    db.Column('followee_id', db.Integer, db.ForeignKey('user.id'))
    )


class User(UserMixin ,db.Model):                ## UserMixin classimizi, flask-login'deki fonksiyonlarimizi User modelimizde kullabilmek amaciyla cagirdik.
    id = db.Column(db.Integer, primary_key= True)
    name= db.Column(db.String(80))
    username= db.Column(db.String(80))
    image= db.Column(db.String(100))
    password= db.Column(db.String(50))
    join_date= db.Column(db.DateTime)

    tweet= db.relationship('Tweet', backref='user', lazy= 'dynamic')
    
    following= db.relationship('User', secondary= follower, 
        primaryjoin=(follower.c.follower_id == id), 
        secondaryjoin=(follower.c.followee_id == id),
        backref= db.backref('followers', lazy= 'dynamic'), lazy= 'dynamic')  

    followed_by= db.relationship('User', secondary= follower,
        primaryjoin=(follower.c.followee_id == id), 
        secondaryjoin=(follower.c.follower_id == id),
        backref= db.backref('followees', lazy= 'dynamic'), lazy= 'dynamic')         

class Tweet(db.Model):                                                         
    id= db.Column(db.Integer, primary_key= True)
    user_id= db.Column(db.Integer, db.ForeignKey('user.id'))    ##burada foreign key'imizin, user modelimizdeki id column'ina karsilik geldigini belirtiyoruz. 
    text= db.Column(db.String(140))
    date_created= db.Column(db.DateTime)


class TweetForm(FlaskForm):
    tweet= TextAreaField('Tweet: ', validators=[InputRequired('Lutfen gecerli bir tweet giriniz.')]) 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegisterForm(FlaskForm):
    
    name= StringField('Isim-Soyisim: ', 
    validators=
    [InputRequired('Lutfen isminizi yazin...'), 
    Length(max=100, message='Isminiz 100 karakterden uzun olamaz.')])
    
    username= StringField('Kullanici Adi:', 
    validators=[InputRequired('Lutfen gecerli bir kullanici adi giriniz.'), 
    Length(max=30, message='Kullanici Adiniz 30 karakterden uzun olamaz.')])

    password= PasswordField('Sifre: ', 
    validators=
    [InputRequired('Lutfen bir sifre belirleyin')])
    
    image = FileField(validators=[FileAllowed(IMAGES, 'Dosya formati olarak yalnizca .jpg, .jpeg, .png vb. görüntü dosya formatlari kabul edilmektedir.')])

class LoginForm(FlaskForm):
    username= StringField('Kullanici Adi:', 
    validators=[InputRequired('Lutfen gecerli bir kullanici adi giriniz.'), 
    Length(max=30, message='Kullanici Adiniz 30 karakterden uzun olamaz.')])
    
    password= PasswordField('Sifre: ', 
    validators=
    [InputRequired('Lutfen bir sifre girin')])

    remember_me= BooleanField('Beni Hatirla ')

@app.route('/')
def index():
    form = LoginForm()
    return render_template('index.html', form= form)

@app.route('/login', methods= ['POST', 'GET'])
def login():
    form= LoginForm()
    
    if request.method == 'GET':
        return redirect(url_for('index'))
    
    if form.validate_on_submit():
        user= User.query.filter_by(username= form.username.data).first()
        
        if not user:
            flash('Boyle bir kullanici bulunmamaktadir.', 'danger')
            return redirect(url_for('index'))
        if check_password_hash(user.password, form.password.data):      ## Burada kriptolanmis sifremizi cozuyor ve cozulmus hali ile gercek sifre uyusuyor mu test ediyoruz.
            login_user(user, remember= form.remember_me.data)
            return redirect(url_for('profile'))  
        
        flash('Hatali Sifre!', 'danger')
        return redirect(url_for('index')) 
    
    return redirect(url_for('index'))       ## Burada da form.validate calismaz ise; kullanicimizi index sayfamiza yonlendiriyoruz.         

@app.route('/logout')
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('index'))



@app.route('/profile', defaults= { 'username' : None })
@app.route('/profile/', defaults= { 'username' : None })
@app.route('/profile/<username>')
@login_required
def profile(username):
    current_time = datetime.now()
    if username:
        try:
            user= User.query.filter_by(username= username).first()
            tweets= Tweet.query.filter_by(user_id= user.id).order_by(Tweet.date_created.desc()).all()
            takipci= user.followed_by.all()
            takip_et= user.following.all()
        except:
            flash('Böyle bir kullanıcı bulunmamaktadır.', 'warning')
            
            user= current_user
            tweets= Tweet.query.filter_by(user_id= current_user.id).order_by(Tweet.date_created.desc()).all()
            takipci= user.followed_by.all()
            takip_et= user.following.all()
    else:
        user= current_user
        takipci= user.followed_by.all()
        takip_et= user.following.all()
        tweets= Tweet.query.filter_by(user_id= current_user.id).order_by(Tweet.date_created.desc()).all()

    return render_template('profile.html', user = user, tweets= tweets, current_time= current_time, takipci= takipci, takip_et= takip_et)      # Buradaki current_user komutumuz ile mevcut kullanici objemizi cagiriyoruz. ( ileride current_user.name gibi kullanicimizin yalnizca ismini vb. cagirabiliriz.)

@app.route('/register', methods= ['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        image_filename= photos.save(form.image.data)
        image_url= photos.url(image_filename)

        newUser= User(name= form.name.data, username= form.username.data,image= image_url, password= generate_password_hash(form.password.data), join_date= datetime.now())
        db.session.add(newUser)
        db.session.commit()

        return redirect(url_for('profile'))

    return render_template('register.html', form=form)

@app.template_filter('how_long_since')
def how_long_since(delta):

    seconds= delta.total_seconds()

    days, seconds= divmod(seconds, 86400)
    hours, seconds= divmod(seconds, 3600)
    minutes, seconds= divmod(seconds, 60)

    if days > 0:
        return '%d Gün Önce' % (days)
    elif hours > 0:
        return '%d Saat Önce' % (hours)
    elif minutes > 0:
        return '%d Dakika Önce' % (minutes)
    else:
        return 'Just Now'


@app.route('/timeline', defaults= { 'username' : None })
@app.route('/timeline/', defaults= { 'username' : None })
@app.route('/timeline/<username>')
def timeline(username):
    form = TweetForm()
    
    if username:
        try:
            user= User.query.filter_by(username= username).first()
            user_id= user.id
        except:
            flash('Boyle bir kullanici bulunmamaktadir.', 'warning')
            user= current_user
            user_id= current_user.id
    else:
        user= current_user
        user_id= current_user.id
    

    tweets= Tweet.query.filter_by(user_id= user_id).order_by(Tweet.date_created.desc()).all()
    total_tweets= len(tweets)

    date= datetime.now()

    return render_template('timeline.html', form= form, tweets= tweets, date= date, total_tweets= total_tweets, user= user)

@app.route('/posttweet', methods= ['POST', 'GET'])
def posttweet():
    form= TweetForm()

    if form.validate_on_submit():
        tweet= Tweet( user_id= current_user.id, text= form.tweet.data, date_created= datetime.now() )
        db.session.add(tweet)
        db.session.commit()
        flash('Tweetiniz başarı ile gönderildi.', 'success')
        return redirect(url_for('timeline'))
    flash('Bir seyler yanlis gitti.', 'danger')
    return redirect(url_for('timeline'))

@app.route('/follow/<username>', methods= ['POST', 'GET'])
@app.route('/follow', defaults= { 'username' : None } )
@login_required
def follow(username):
    if username: 
        user_to_follow= User.query.filter_by(username= username).first()

        current_user.following.append(user_to_follow)
        
        db.session.commit()
        
        flash('takip islemi basarili', 'success')
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('profile'))
if __name__ == "__main__":
    manager.run()


    