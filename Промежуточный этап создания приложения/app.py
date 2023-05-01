from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    works = db.relationship('Work', backref='author', lazy=True)


class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    works = db.relationship('Work', backref='department', lazy=True)


department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)


@app.before_first_request
def create_tables():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        user = User(username=request.form['username'], email=request.form['email'], password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Успешно зарегистрированы! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Не удалось войти. Проверьте свой адрес электронной почты и пароль.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/add_work', methods=['GET', 'POST'])
@login_required
def add_work():
    if request.method == 'POST':
        work = Work(title=request.form['title'], content=request.form['content'], author=current_user)
        db.session.add(work)
        db.session.commit()
        flash('Работа успешно добавлена!', 'success')
        return redirect(url_for('home'))
    return render_template('add_work.html')


@app.route('/')
@app.route('/home')
def home():
    works = Work.query.all()
    return render_template('home.html', works=works)


@app.route('/edit_work/<int:work_id>', methods=['GET', 'POST'])
@login_required
def edit_work(work_id):
    work = Work.query.get_or_404(work_id)
    if work.author != current_user and current_user.id != 1:
        abort(403)
    if request.method == 'POST':
        work.title = request.form['title']
        work.content = request.form['content']
        db.session.commit()
        flash('Работа успешно отредактирована!', 'success')
        return redirect(url_for('home'))
    return render_template('add_work.html', work=work, edit=True)


@app.route('/delete_work/<int:work_id>', methods=['POST'])
@login_required
def delete_work(work_id):
    work = Work.query.get_or_404(work_id)
    if work.author != current_user and current_user.id != 1:
        abort(403)
    db.session.delete(work)
    db.session.commit()
    flash('Работа успешно удалена!', 'success')
    return redirect(url_for('home'))

@app.route('/departments', methods=['GET'])
def departments():
    departments = Department.query.all()
    return render_template('departments.html', departments=departments)


@app.route('/add_department', methods=['GET', 'POST'])
@login_required
def add_department():
    if request.method == 'POST':
        department = Department(name=request.form['name'])
        db.session.add(department)
        db.session.commit()
        flash('Департамент успешно добавлен!', 'success')
        return redirect(url_for('departments'))
    return render_template('add_department.html')


@app.route('/edit_department/<int:department_id>', methods=['GET', 'POST'])
@login_required
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    if request.method == 'POST':
        department.name = request.form['name']
        db.session.commit()
        flash('Департамент успешно обновлен!', 'success')
        return redirect(url_for('departments'))
    return render_template('edit_department.html', department=department)


@app.route('/delete_department/<int:department_id>', methods=['POST'])
@login_required
def delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    db.session.delete(department)
    db.session.commit()
    flash('Департамент успешно удален!', 'success')
    return redirect(url_for('departments'))


if __name__ == '__main__':
    app.run(debug=True)
