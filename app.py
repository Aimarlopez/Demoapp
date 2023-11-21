import os
from datetime import datetime

from flask import Flask, redirect, render_template, request, send_from_directory, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__, static_folder='static')
csrf = CSRFProtect(app)

# WEBSITE_HOSTNAME exists only in production environment
if 'WEBSITE_HOSTNAME' not in os.environ:
    # local development, where we'll use environment variables
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    # production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize the database connection
db = SQLAlchemy(app)

# Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
migrate = Migrate(app, db)

# The import must be done after db initialization due to circular import issue
from models import Item, amount

@app.route('/', methods=['GET'])
def index():
    print('Request for index page received')
    Items = Item.query.all()
    return render_template('index.html', Items=Items)

@app.route('/<int:id>', methods=['GET'])
def details(id):
    Item = Item.query.where(Item.id == id).first()
    amounts = amount.query.where(amount.Item == id)
    return render_template('details.html', Item=Item, amounts=amounts)

@app.route('/create', methods=['GET'])
def create_Item():
    print('Request for add item page received')
    return render_template('create_Item.html')

@app.route('/add', methods=['POST'])
@csrf.exempt
def add_Item():
    try:
        name = request.values.get('Item_name')
        street_address = request.values.get('item_type')
        description = request.values.get('description')
    except (KeyError):
        # Redisplay the question voting form.
        return render_template('add_item.html', {
            'error_message': "You must include a item name, type, and description",
        })
    else:
        Item = Item()
        Item.name = name
        Item.street_address = street_address
        Item.description = description
        db.session.add(Item)
        db.session.commit()

        return redirect(url_for('details', id=Item.id))

@app.route('/amount/<int:id>', methods=['POST'])
@csrf.exempt
def add_amount(id):
    try:
        user_name = request.values.get('user_name')
        rating = request.values.get('rating')
        amount_text = request.values.get('amount_text')
    except (KeyError):
        #Redisplay the question voting form.
        return render_template('add_amount.html', {
            'error_message': "Error adding amount",
        })
    else:
        amount = amount()
        amount.Item = id
        amount.amount_date = datetime.now()
        amount.user_name = user_name
        amount.rating = int(rating)
        amount.amount_text = amount_text
        db.session.add(amount)
        db.session.commit()

    return redirect(url_for('details', id=id))

@app.context_processor
def utility_processor():
    def star_rating(id):
        amounts = amount.query.where(amount.Item == id)

        ratings = []
        amount_count = 0
        for amount in amounts:
            ratings += [amount.rating]
            amount_count += 1

        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        stars_percent = round((avg_rating / 5.0) * 100) if amount_count > 0 else 0
        return {'avg_rating': avg_rating, 'amount_count': amount_count, 'stars_percent': stars_percent}

    return dict(star_rating=star_rating)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()
