from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from database_setup import Base, Catalog, Item, User
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import random
import string
from functools import wraps
from flask import (Flask, render_template, g, request,
                   redirect, jsonify, url_for, flash)

app = Flask(__name__)
app.secret_key = '_5#y2L"F4Q8z\n\xec]/'


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Connect to Database and create database session
engine = create_engine('sqlite:///itemscatalog.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
Session = scoped_session(DBSession)
session = Session()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))
    # If there was an erlinror in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is/'
                                 ' already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ''' " style = "width: 300px; height: 300px;border-radius: 150px;
    -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '''
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print('Access Token is None')
        response = make_response(json.dumps('Current user not/'
                                            'connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print('In gdisconnect access token is %s', access_token)
    print('User name is: ')
    print(login_session['username'])
    urlstr = 'https://accounts.google.com/o/oauth2/revoke?token=%s'
    url = urlstr % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print('result is ')
    print(result)
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke/'
                                            ' token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Shows a list of all the catalogs
@app.route('/')
@app.route('/catalogs')
def showCatalogs():
    catalogs = session.query(Catalog).all()
    rows = session.query(Catalog).count()
    return render_template(
            'index.html', catalog=catalogs, size_table=rows)


# List all the items in the catalog
@app.route('/<int:catalog_id>')
@app.route('/<int:catalog_id>/items')
def showItems(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).first()
    rows = session.query(Item).filter_by(id=catalog_id).count()
    items = session.query(Item).filter_by(catalog=catalog).all()
    return render_template('items.html', items=items,
                           catalog=catalog, size_table=rows)


# Description of a particular item
@app.route('/<int:catalog_id>/<string:item_name>')
def viewItem(catalog_id, item_name):
    item = session.query(Item).filter_by(
            catalog_id=catalog_id, name=item_name).first()
    return render_template('view-item.html', item=item)


def loginCheck():
    if 'username' not in login_session:
        return redirect('/login')

# Edit the item
@app.route('/<int:catalog_id>/<string:item_name>/edit',
           methods=['GET', 'POST'])
def editItem(catalog_id, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Catalog).filter_by(id=catalog_id).first()
    item = session.query(Item).filter_by(
            catalog_id=catalog.id, name=item_name).first()
    itemOfUser = item.user_id
    user = session.query(User).filter_by(id=itemOfUser).first()
    if login_session['username'] != user.name:
        return redirect(url_for('editError'))
    print("\n\n\nitem", item)
    if request.method == 'POST':
        if request.form['name'] == '' and request.form['description'] != '':
            item.description = request.form['description']
            return redirect(url_for('showCatalogs'))
        elif request.form['description'] == '' and request.form['name'] != '':
            item.name = request.form['name']
            return redirect(url_for('showCatalogs'))
        else:
            item.name = request.form['name']
            item.description = request.form['description']
            try:
                session.commit()
            except:
                session.rollback()
                raise
            return redirect(url_for('showCatalogs'))
    else:
        return render_template('edit.html', catalog=catalog, item=item)


@app.route('/not-editable')
def editError():
    return render_template('edit-error.html')


# Delete the item
@app.route('/<int:catalog_id>/<string:item_name>/delete',
           methods=['GET', 'POST'])
def deleteItem(catalog_id, item_name):
    catalog = session.query(Catalog).filter_by(id=catalog_id).first()
    item = session.query(Item).filter_by(
            catalog_id=catalog.id, name=item_name).first()
    itemOfUser = item.user_id
    user = session.query(User).filter_by(id=itemOfUser).first()
    if 'username' not in login_session:
        return redirect('/login')
    if login_session['username'] != user.name:
        return redirect(url_for('deleteError'))
    if request.method == 'POST':
        itemOfUser = item.user_id
        user = session.query(User).filter_by(id=itemOfUser).first()
        session.delete(item)
        try:
            session.commit()
        except:
            session.rollback()
            raise
        return redirect(url_for('showCatalogs'))
    else:
        return render_template(
                'delete.html', catalog_id=catalog.id, item_name=item.name)


@app.route('/not-deletable')
def deleteError():
    return render_template('delete-error.html')


# Add a new item
@app.route('/add', methods=['GET', 'POST'])
def addItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name'] == '' or request.form['catalog'] == '':
            return redirect(url_for('addItem'))
        else:
            cat = session.query(Catalog).filter_by(
                    name=request.form['catalog']).first()
            newItem = Item(
                        name=request.form['name'],
                        description=request.form['description'],
                        catalog=cat,
                        user=User(name=login_session['username'])
                        )
            session.add(newItem)
            try:
                session.commit()
            except:
                session.rollback()
                raise
            return redirect(url_for('showCatalogs'))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('add.html', catalogs=catalogs)


# Add a new catalog
@app.route('/add-catalog', methods=['GET', 'POST'])
def addCatalog():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        if request.form['name'] == '':
            return redirect(url_for('addCatalog'))
        else:
            newCat = Catalog(name=request.form['name'])
            session.add(newCat)
            try:
                session.commit()
            except:
                session.rollback()
                raise
            return redirect(url_for('showCatalogs'))
    else:
        catalogs = session.query(Catalog).all()
        return render_template('add-catalog.html')


# API endpoint of the catalog
@app.route('/API/v1/catalog')
def apiCatalogs():
    catalogs = session.query(Catalog).all()
    return jsonify(Catalog=[c.serialize for c in catalogs])


@app.route('/API/v1/<int:catalog_id>')
def apiItemsCatalog(catalog_id):
    items = session.query(Item).filter_by(catalog_id=catalog_id).all()
    return jsonify(Item=[i.serialize for i in items])


@app.route('/API/v1/item/<int:item_id>')
def apiItem(item_id):
    item = session.query(Item).filter_by(id=item_id).first()
    return jsonify(item.serialize)


if __name__ == '__main__':
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    app.run()
