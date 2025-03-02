from flask import Flask,redirect,url_for,render_template,session,flash,request
from forms import RegistrationForm, LoginForm, InputForm
from flask_bcrypt import Bcrypt
from database import User, db , TrackerInput
from model.model import prediction_cancer
import os
app = Flask(__name__)

app.config['SECRET_KEY'] ='1234$'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)
bcrypt = Bcrypt(app)

# @app.before_request
# def check_auth():
#     block_route = ['/input','/predict','/result','/history']
#     if 'username'  not in session and request.path in block_route:
#         return redirect(url_for('login'))


def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session:
            flash('You need to login first!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST','GET'])
def register():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # hash
        hashed_password = bcrypt.generate_password_hash(password).decode('utf8')
        #create record 
        new_user = User(username=username, password=hashed_password)
        # add commit
        db.session.add(new_user)
        db.session.commit()
        flash('Register Successfull')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods = ['POST','GET'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user_check = User.query.filter_by(username=username).first()
        if user_check and bcrypt.check_password_hash(user_check.password, password):
            session['username'] = username
            return redirect(url_for('input'))
    return render_template('login.html',form=form)

@app.route('/input')
@login_required
def input():
    form = InputForm()
    return render_template('input.html',form = form)



@app.route('/predict', methods=['POST','GET'])
@login_required
def predict():
    form = InputForm()
    if request.method == 'POST':
        Average_Income = form.Average_Income.data
        Ad_Spend_per_Car = form.Ad_Spend_per_Car.data
        Sales_to_Income_Ratio = form.Sales_to_Income_Ratio.data


        features = [
            Average_Income,Ad_Spend_per_Car,Sales_to_Income_Ratio
        ]

        predicted_class = prediction_cancer(features)
        username_login = session['username']
        user_check = User.query.filter_by(username =username_login ).first()
        new_input = TrackerInput(
            user_id= user_check.id,
            Average_Income = Average_Income,
            Ad_Spend_per_Car = Ad_Spend_per_Car ,
            Sales_to_Income_Ratio = Sales_to_Income_Ratio ,
            result = predicted_class
        )
        db.session.add(new_input)
        db.session.commit()


    return redirect(url_for('result' , predicted_class =predicted_class) )


@app.route('/result')
@login_required
def result():
    predicted_class = request.args.get('predicted_class')
    return render_template('result.html', predicted_class=predicted_class)


@app.route('/history')
@login_required
def history():
    if 'username' in session :
        username_login = session['username']
        user_check = User.query.filter_by(username =username_login ).first()
        inputs = TrackerInput.query.filter_by(user_id = user_check.id).all()
        return render_template('history.html',inputs = inputs)
    return redirect(url_for('login'))    

@app.route('/logout')
@login_required
def logout():
    session.pop('username')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)