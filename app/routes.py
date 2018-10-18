import reprlib
from datetime import datetime

from flask import render_template, flash, redirect, url_for, request, Response
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from werkzeug.exceptions import abort
from app import app, db
from app.forms import (LoginForm, RegistrationForm, ResetPasswordRequestForm,
                       ResetPasswordForm, BookForm)
from app.email import send_password_reset_email
from app.models import User, Book
from app.cover import get_isbn

def check(ltype):

    if ltype not in ('current', 'history', 'planned'):
        abort(404)

@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('listview', list_type='current'))
    return render_template('index.html', title='Reading list')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('listview', list_type='current'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('listview', list_type='current')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('listview', list_type='current'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('listview', list_type='current'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('listview', list_type='current'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/list/<list_type>')
@login_required
def listview(list_type):

    if list_type == 'current':
        bks_obj = current_user.books.filter_by(list=1) \
                  .order_by(Book.timestamp.desc())
    elif list_type == 'history':
        bks_obj = current_user.books.filter_by(list=2) \
                  .order_by(Book.timestamp.desc())
    elif list_type == 'planned':
        bks_obj = current_user.books.filter_by(list=3) \
                  .order_by(Book.timestamp.desc())
    else:
        abort(404)

    page = request.args.get('page', 1, type=int)
    books = bks_obj.paginate(page, app.config['TITLES_PER_PAGE'], False)

    next_url = url_for('listview', list_type=list_type, page=books.next_num) \
            if books.has_next else None
    prev_url = url_for('listview', list_type=list_type, page=books.prev_num) \
            if books.has_prev else None

    lis = list_type.capitalize()
    num = app.config['TITLES_PER_PAGE'] * (page - 1) + 1

    return render_template('listview.html', title=f'Reading list - {lis}',
                           books=books.items, list_type=list_type,
                           next_url=next_url, prev_url=prev_url, num=num,
                           page=page)

@app.route('/<list_type>/detail/<id>')
@login_required
def detail(list_type, id):

    book = Book.query.get_or_404(int(id))
    page = request.args.get('page', 1, type=int)

    # What happens when user presses the `back` button after moving to
    # another list.
    if list_type != 'others':
        ltype = ('current', 'history', 'planned').index(list_type) + 1
        if book.list != ltype:
            abort(Response(
                f'<h2>Error: id {id} not in list {list_type!r}.</h2>'
            ))

    return render_template('detail.html', title='Book details',
                           book=book, list_type=list_type, page=page)

@app.route('/<list_type>/add', methods=['GET', 'POST'])
@login_required
def add(list_type):

    check(list_type)
    form = BookForm()

    if form.validate_on_submit():
        ltype = ('current', 'history', 'planned').index(list_type) + 1
        if list_type == 'current':
            private_data = form.private.data
        else:
            private_data = True

        book = Book(title=form.title.data,
                    user_id=current_user.id,
                    author=form.author.data,
                    edition=form.edition.data,
                    format=int(form.format.data),
                    about=form.about.data,
                    private=private_data,
                    list=ltype)

        if form.cover.data:
            book.isbn = get_isbn(form.title.data, form.author.data)
        else:
            book.isbn = None

        db.session.add(book)
        db.session.commit()
        flash('The book was added to the list.')
        return redirect(url_for('listview', list_type=list_type))

    return render_template('book.html', title='Add book',
                           form=form, list_type=list_type, heading='Add')

@app.route('/to-list/<list_type>/<id>')
@login_required
def to_list(list_type, id):

    check(list_type)
    if list_type == 'history': abort(404)
    book = Book.query.get_or_404(id)

    if list_type == 'current':
        book.list = 2
        moved_to = 'history'
    elif list_type == 'planned':
        book.list = 1
        moved_to = 'current'

    book.timestamp = datetime.utcnow()
    db.session.commit()

    flash(f'Book moved to list {moved_to!r}.')
    page = request.args.get('page', 1, type=int)

    return redirect(url_for('listview', list_type=list_type, page=page))

@app.route('/<list_type>/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit(list_type, id):

    check(list_type)
    book = Book.query.get_or_404(id)
    form = BookForm()

    if form.validate_on_submit():
        if list_type == 'current':
            private_data = form.private.data
        else:
            private_data = True

        flag = False
        if ((book.title != form.title.data and form.cover.data) or
                (book.author != form.author.data and form.cover.data) or
                (book.isbn is None and form.cover.data)):
            book.isbn = get_isbn(form.title.data, form.author.data)
            if not book.isbn: flag = True
        elif form.cover.data is False:
            book.isbn = None

        book.title = form.title.data
        book.author = form.author.data
        book.edition = form.edition.data
        book.format = int(form.format.data)
        book.about = form.about.data
        book.private = private_data

        db.session.commit()

        if flag:
            flash('Your changes, other than cover image indicator,'
                  ' were saved.')
        else:
            flash('Your changes have been saved.')

        page = request.args.get('page', 1, type=int)

        return redirect(url_for('detail', list_type=list_type, id=id,
                                page=page))
    elif request.method == 'GET':
        form.title.data = book.title
        form.author.data = book.author
        form.edition.data = book.edition
        form.format.data = str(book.format)
        form.about.data = book.about
        form.private.data = book.private
        form.cover.data = True if book.isbn else False

    return render_template('book.html', title='Edit book', id=id,
                           form=form, list_type=list_type, heading='Edit')

@app.route('/<list_type>/delete/<id>')
@login_required
def delete(list_type, id):

    check(list_type)
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()

    title = reprlib.repr(book.title)
    flash(f'Book {title} was deleted.')
    page = request.args.get('page', 1, type=int)

    return redirect(url_for('listview', list_type=list_type, page=page))

@app.route('/others')
@login_required
def others():

    page = request.args.get('page', 1, type=int)
    books = Book.query.filter_by(list=1, private=False) \
                      .filter(Book.user_id != current_user.id) \
                      .order_by(Book.timestamp.desc()) \
                      .paginate(page, app.config['TITLES_PER_PAGE'], False)

    next_url = url_for('others', page=books.next_num) \
               if books.has_next else None
    prev_url = url_for('others', page=books.prev_num) \
               if books.has_prev else None

    return render_template('others.html', title='Reading list - Others',
                           books=books.items, next_url=next_url,
                           prev_url=prev_url, page=page)
