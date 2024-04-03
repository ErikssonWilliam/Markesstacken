 #!/usr/bin/env python3
from datetime import datetime
from flask import Flask
from flask import jsonify
from flask import abort
from flask import request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_bcrypt import generate_password_hash
from flask_bcrypt import check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__, static_folder='../client', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_secret_key' 

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    firstName = db.Column(db.String, nullable=False)
    lastName = db.Column(db.String, nullable=False)
    #ShoppingCartID = db.relationship('ShoppingCart', backref='shopping_cart', lazy=True, uselist=False)
    #paymentID = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)
    #orderID = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)

    def __repr__(self):
        return f'<User {self.id}: {self.name} ({self.email})>'

    def serialize(self):
        return dict(id=self.id, name=self.name, email=self.email, is_admin=self.is_admin)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf8')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String, nullable=False)
    model = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = True)

    user = db.relationship('User', backref='user_cars', lazy=True)

    def __repr__(self):
        return f'<Car {self.id}: {self.make} {self.model}>'

    def serialize(self):
        return dict(id=self.id, make=self.make, model=self.model, user_id=self.user_id)

class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', backref='subcategories', lazy=True)
    productID = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True) #nullable???

    def __repr__(self):
        return f'<Subcategory {self.id}: {self.name}: {self.category}>'
    
    def serialize(self):
        return dict(
            id=self.id, 
            name=self.name, 
            category=self.category.serialize() if self.category else None
        )

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'

    def serialize(self):
        return dict(id=self.id, name=self.name)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String, nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)

    def __repr__(self):
        return f'<Product {self.id}: {self.name} ({self.price})>'

    def serialize(self):
        return dict(id=self.id, name=self.name, price=self.price, description=self.description)

with app.app_context():
    db.drop_all() #Remove before production
    db.create_all()
    db.session.commit()

    #THIS IS FOR DEFAULT CATEGORIES OR TESTING
    category1 = Category(name='Kravaller')
    category2 = Category(name='Övrigt')
    db.session.add(category1)
    db.session.add(category2)
    subcat1 = Subcategory(name='UK', category=category1)
    subcat2 = Subcategory(name='Festivallen', category=category1)
    db.session.add(subcat1)
    db.session.add(subcat2)

    db.session.commit()

@app.route('/subcategories', methods=['GET', 'POST'], endpoint='subcategories')
#@jwt_required()
def subcategories():
    if request.method == 'GET':
        subcategories = Subcategory.query.all()
        subcategory_list = [subcategory.serialize() for subcategory in subcategories]
        return jsonify(subcategory_list)

    elif request.method == 'POST' and get_jwt_identity().is_admin:
        data = request.get_json()
        new_subcategory = Subcategory(name=data['name'], category_id=data['category_id'])
        db.session.add(new_subcategory)
        db.session.commit()
        return jsonify(new_subcategory.serialize()), 201

@app.route('/subcategories/<int:subcategory_id>', methods=['GET', 'PUT', 'DELETE'], endpoint='subcategory_by_id')
#@jwt_required()
def subcategory_by_id(subcategory_id):
    subcategory = Subcategory.query.get_or_404(subcategory_id)

    if request.method == 'GET':
        return jsonify(subcategory.serialize())

    elif request.method == 'PUT' and get_jwt_identity().is_admin:
        data = request.get_json()
        if 'name' in data:
            subcategory.name = data['name']
        if 'category_id' in data:
            subcategory.category_id = data['category_id']
        db.session.commit()
        return jsonify(subcategory.serialize()), 200

    elif request.method == 'DELETE' and get_jwt_identity().is_admin:
        db.session.delete(subcategory)
        db.session.commit()
        return jsonify("Success!"), 200

@app.route('/categories', methods=['GET', 'POST'], endpoint='categories')
#@jwt_required()
def categories():
    if request.method == 'GET':
        categories = Category.query.all()
        category_list = [category.serialize() for category in categories]
        return jsonify(category_list)

    elif request.method == 'POST' and get_jwt_identity().is_admin:
        data = request.get_json()
        new_category = Category(name=data['name'])
        db.session.add(new_category)
        db.session.commit()
        return jsonify(new_category.serialize()), 201
    
@app.route('/categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'], endpoint='category_by_id')
#@jwt_required()
def category_by_id(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == 'GET':
        return jsonify(category.serialize())

    elif request.method == 'PUT' and get_jwt_identity().is_admin:
        data = request.get_json()
        if 'name' in data:
            category.name = data['name']
        db.session.commit()
        return jsonify(category.serialize()), 200

    elif request.method == 'DELETE' and get_jwt_identity().is_admin:
        db.session.delete(category)
        db.session.commit()
        return jsonify("Success!"), 200

@app.route('/sign-up', methods=['POST'])
def sign_up():
    data = request.get_json()

    if 'email' not in data or 'name' not in data or 'password' not in data:
        return jsonify({"error": "Missing required fields"}), 400  # 400 Bad Request
    email = data['email']
    name = data['name']
    password = data['password']

    # Create a new user
    new_user = User(email=email, name=name)
    new_user.set_password(password)

    # Save the new user to the database
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=new_user.id)

    return jsonify({"message": "User created successfully", "access_token": access_token}), 201  # 200 OK


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if 'email' not in data or 'password' not in data:
        return jsonify({"error": "Missing required fields"}), 400  # 400 Bad Request

    email = data['email']
    password = data['password']

    user = User.query.filter_by(email=data['email']).first()

    if user and user.check_password(password):
        # Password is correct, generate an access token
        access_token = create_access_token(identity=user.id)

        # Return the token and user data (excluding password hash)
        response = {
            'token' : access_token,
            'user' : user.serialize()
        }
        return jsonify(response)
    else:
        return jsonify({"error": "Invalid email or password"}), 401  # 401 Unauthorized


# @app.route('/cars/<int:car_id>', methods=['PUT', 'GET', 'DELETE'], endpoint='get_car_by_id')
# @jwt_required()
# def get_car_by_id(car_id):
#     current_user = get_jwt_identity()
#     car = Car.query.get_or_404(car_id)
 
#     if request.method == 'GET':
#         car_data = car.serialize()

#         if car.user:
#             car_data['user'] = car.user.serialize()
#         else:
#             car_data['user'] = None

#         car_data.pop('user_id', None)

#         return jsonify(car_data)

#     elif request.method == 'PUT':
#         data = request.get_json()

#         if 'make' in data:
#             car.make = data['make']
            
#         if 'model' in data:
#             car.model = data['model']

#         if 'user_id' in data:
#             user_id = data['user_id']
#             user = None  # Initialize user variable

#             if user_id:  # Check if user_id is provided
#                 user = User.query.get(user_id)

#                 if user is None:
#                     abort(404)

#             car.user_id = user.id if user else None

#         db.session.commit()
#         return jsonify(car.serialize()), 200


#     elif request.method == 'DELETE':
#         db.session.delete(car)
#         db.session.commit()
#         return jsonify("Success!"), 200

# @app.route('/cars/<int:car_id>/booking', methods=['POST'], endpoint = 'book_car')
# @jwt_required()
# def book_car(car_id):

#     car = Car.query.get_or_404(car_id)

#     if request.method == 'POST':
#         current_user = get_jwt_identity()
#         data = request.get_json()

#         if car.user_id:
#             abort(400, "Car already booked")

#         car.user_id = data['user_id']
#         db.session.commit()

#         return jsonify({"message": "Car booked successfully"}), 200

# @app.route('/cars', methods=['GET', 'POST'], endpoint = 'cars')
# @jwt_required()
# def cars():

#   if request.method == 'GET':
#      # Handle GET request
#     cars = Car.query.all()
#     car_list = []

#     for car in cars:
#         car_data = car.serialize()

#         if car.user:
     
#             car_data['user_id'] = car.user.serialize()
#         else:

#             car_data['user_id'] = None

#         car_list.append(car_data)

#     return jsonify(car_list)

#   elif request.method == 'POST' :

#     data = request.get_json()
#     user_id = data.get('user_id', None)

#     new_car = Car(make=data['make'], model=data['model'], user_id=user_id)
#     db.session.add(new_car)
#     db.session.commit()

#     return jsonify(new_car.serialize()), 201 

@app.route('/users', methods=['GET', 'POST'], endpoint = 'users')
#@jwt_required()
def users():
    if request.method == 'GET':
        # Handle GET request
        users = User.query.all()
        user_list = [user.serialize() for user in users]
        return jsonify(user_list)

    elif request.method == 'POST':
        # Handle POST request
        data = request.get_json()

        new_user = User(name=data['name'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify(new_user.serialize()), 201

@app.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'], endpoint = 'get_user_by_id')
@jwt_required()
def get_user_by_id(user_id):
    current_user = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        abort(404)

    if request.method == 'GET':
        return jsonify(user.serialize())

    elif request.method == 'PUT':
        data = request.get_json()
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        if 'is_admin' in data:
            user.is_admin = data['is_admin']

        db.session.commit()
        return jsonify(user.serialize()), 200

    elif request.method == 'DELETE':
        user_id = user.id

        # cars_to_reset = Car.query.filter_by(user_id=user_id).all()

        # for car in cars_to_reset:
        #     car.user = None

        db.session.delete(user)
        db.session.commit()
        return jsonify("Success!"), 200

@app.route('/users/<int:user_id>/cars', methods=['GET'], endpoint = 'get_cars_by_user')
@jwt_required()
def get_cars_by_user(user_id):

    user = User.query.get(user_id)

    if not user:
        abort(404)

    if request.method == 'GET' :

     cars = user.cars
     car_list = []

    for car in cars:
        car_data = car.serialize()

        car_list.append(car_data)
        car_data.pop('user_id', None)

    return jsonify(car_list)

#labb2
@app.route("/")
def client():
    return app.send_static_file("client.html")



if __name__ == "__main__":
    app.run(port=5001) # På MacOS, byt till 5001 eller dylikt

