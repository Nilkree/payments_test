from flask import Flask, request, render_template, g
import hashlib
import requests
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from contextlib import closing
from datetime import datetime

SHOP_ID = '300945'
SECRET = 'QwiYF361HrI5MkSeeDILfitWVyj8QIF9G'

app = Flask(__name__)
app.config.from_pyfile('main.cfg')


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


def get_sign(data, keys_required, secret):
    keys_sorted = sorted(keys_required)
    string_to_sign = (":".join([str(data[k]) for k in keys_sorted])+':' + secret).encode('utf8')
    sign = hashlib.md5(string_to_sign).hexdigest()
    return sign


@app.route('/', methods=['GET', 'POST'])
def main_page():
    error = None
    # print(request.method)
    if request.method == 'POST':
        if request.form['currency'] == 'RUB':
            keys_required = ['amount', 'currency', 'shop_id', 'shop_invoice_id']
            data = {"shop_id": SHOP_ID,
                    "amount": request.form['amount'],
                    "currency": 643,
                    'shop_invoice_id': 1
                    }

            sign = get_sign(data, keys_required, SECRET)
            data['sign'] = sign
            data['description'] = request.form['description']
            g.db.execute('insert into payments (amount, currency, date, description) values (?, ?, ?, ?)',
                 [data['amount'], data['currency'], datetime.now().isoformat(), data['description']])
            g.db.commit()

            # print(sign)
            app.logger.info('Send user to pay with currency %s', request.form['currency'])
            return render_template('redirect_page.html', data=data)
        elif request.form['currency'] == 'UAH':
            keys_required = ['amount',  'currency', 'payway', 'shop_id', 'shop_invoice_id']
            data = {"shop_id": SHOP_ID,
                    "amount": request.form['amount'],
                    "payway": "w1_uah",
                    "currency": 980,
                    'shop_invoice_id': 1
                    }
            sign = get_sign(data, keys_required, SECRET)
            data['sign'] = sign
            data['description'] = request.form['description']
            g.db.execute('insert into payments (amount, currency, date, description) values (?, ?, ?, ?)',
                 [data['amount'], data['currency'], datetime.now().isoformat(), data['description']])
            g.db.commit()
            # print(sign)
            response = requests.post('https://central.pay-trio.com/invoice', json=data)
            if response.status_code != 200:
                # print(response.status_code)
                error = 'Cannot receive invoice'
                app.logger.warning('An error occurred: response with code %s, %s',
                                   response.status_code, response.reason)
            else:
                response = response.json()
                if response['result'] == "error":
                    error = response['message']
                    app.logger.warning('An error occurred: %s', error)
                else:
                    new_data = response['data']
                    app.logger.info('Send user to pay with currency %s', request.form['currency'])
                    return render_template('invoice_redirect.html', data=new_data)
    return render_template('main_page.html', error=error)


if __name__ == '__main__':
    formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")
    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.run()
