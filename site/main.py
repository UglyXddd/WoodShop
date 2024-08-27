from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, FloatField, TextAreaField, FileField, SubmitField, DecimalField
from wtforms.validators import DataRequired, Email, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.file import FileRequired, FileAllowed
import email_validator
import os
from flask import request, redirect, url_for, flash
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage


app = Flask(__name__)
app.config['SECRET_KEY'] = 'we-smoke-woods-and-no-one-will-know'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wood.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


# User loader function
@login_manager.user_loader
def load_user(user_id):
    return UserData.query.get(int(user_id))


class Product(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    discount = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)

    images = db.relationship('ProductImage', backref='product', lazy=True, cascade="all, delete-orphan")


class ProductImage(db.Model):
    image_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)


class ContactMe(db.Model):
    request_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(500), nullable=False)


# Initialize the database with categories
def init_db():
    db.create_all()
    categories = ["Столешницы", "Стулья", "Шкафы", "Кресла", "Принадлежности", "Скамейки", "Кровати", "Декор"]
    for cat_name in categories:
        category = Category(name=cat_name)
        db.session.add(category)
    ##db.session.commit()


class UserData(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    mail = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    second_name = db.Column(db.String(50), nullable=False)
    father_name = db.Column(db.String(50), nullable=True)
    total_purchase = db.Column(db.Float, nullable=True)

    def get_id(self):
        return (self.user_id)

    @property
    def is_authenticated(self):
        # Assume all users are authenticated
        return True

    @property
    def is_active(self):
        # Assume all users are active
        return True

    @property
    def is_anonymous(self):
        # No anonymous users
        return False


class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Review(db.Model):
    review_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_data.user_id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    mark = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)


class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_data.user_id'), primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    images = FileField('Images', validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Images only!')])
    amount = IntegerField('Amount', validators=[DataRequired()])
    description = TextAreaField('Description')
    discount = DecimalField('Discount', validators=[NumberRange(min=0, max=100)])
    status = StringField('Status', validators=[DataRequired()])
    category_id = IntegerField('Category ID', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/')
def index():
    return render_template('index.html')


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    print("Проверка ебать")
    print(filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/registration', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        first_name = request.form['first_name']
        second_name = request.form['second_name']
        father_name = request.form.get('father_name')
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']

        if password != confirm_password:
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = UserData(
            mail=email,
            password_hash=hashed_password,
            first_name=first_name,
            second_name=second_name,
            father_name=father_name
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    return render_template('registration.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = UserData.query.filter_by(mail=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/catalog', methods=['GET'])
def catalog():
    categories = Category.query.all()
    products = Product.query.all()
    return render_template('catalog.html', categories=categories, products=products)


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return 'Файл успешно загружен'
    return 'Ошибка загрузки файла'


@app.route('/products', methods=['GET', 'POST'])
def manage_products():
    form = ProductForm()
    products = Product.query.all()
    if form.validate_on_submit():

        product = Product(
            name=form.name.data,
            price=form.price.data,
            amount=form.amount.data,
            description=form.description.data,
            discount=form.discount.data,
            status=form.status.data,
            category_id=form.category_id.data
        )
        db.session.add(product)
        db.session.flush()

        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)

                    relative_path = os.path.join('uploads', filename).replace('\\', '/')
                    image = ProductImage(product_id=product.product_id, image_url=relative_path)
                    db.session.add(image)

        db.session.commit()

        flash('Product created successfully', 'success')
        return redirect(url_for('manage_products'))

    return render_template('crm.html', form=form, products=products)


@app.route('/products/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('manage_products'))


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        if not name or not email or not message:
            flash('Все поля должны быть заполнены.', 'error')
            return redirect(url_for('contact'))

        if '@' not in email or '.' not in email:
            flash('Введите корректный email.', 'error')
            return redirect(url_for('contact'))

        new_contact = ContactMe(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()

        flash('Сообщение отправлено.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/shopping_cart')
def shopping_cart():
    return render_template('shopping_cart.html')


@app.route('/order_history')
def order_history():
    return render_template('order_history.html')


@app.route('/product/<int:product_id>', endpoint='product_page')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).all()
    if reviews:
        average_rating = round(sum([review.mark for review in reviews]) / len(reviews))
        reviews_count = len(reviews)
    else:
        average_rating = 0
        reviews_count = 0

    return render_template('product_page.html', product=product, average_rating=average_rating, reviews_count=reviews_count)


@app.route('/submit_review/<int:product_id>', methods=['POST'])
def submit_review(product_id):
    content = request.form['review_content']
    review = Review(product_id=product_id, user_id=current_user.user_id, content=content)
    db.session.add(review)
    db.session.commit()
    return redirect(url_for('product_page', product_id=product_id))


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
