"""
Insta485 accounts view.

URLs include:
/accounts/login/
/accounts/logout/
/accounts/create/
/accounts/delete/
/accounts/edit/
/accounts/password/
/accounts/?target=URL
"""
import uuid
import pathlib
import hashlib
import os
import flask
from flask import request, abort
from flask.helpers import url_for
import insta485


@insta485.app.route('/accounts/login/')
def show_login():
    """Display /accounts/login route."""
    if 'username' not in flask.session:
        # notice that render() will return str type
        return flask.render_template("login.html")
    return flask.redirect(flask.url_for('show_index'))


@insta485.app.route('/accounts/logout/', methods=['POST'])
def handle_logout():
    """Log out the user, immediate redirect to login page."""
    flask.session.clear()
    return flask.redirect(flask.url_for('show_login'))


@insta485.app.route('/accounts/create/')
def show_create():
    """Display /accounts/create route."""
    if 'username' not in flask.session:
        return flask.render_template("create.html")

    return flask.redirect(flask.url_for('show_edit'))


@insta485.app.route('/accounts/delete/')
def show_delete():
    """Display /accounts/delete route."""
    if 'username' not in flask.session:
        return flask.redirect(url_for('show_login'))

    logname = flask.session['username']
    content = {'logname': logname}
    return flask.render_template("delete.html", **content)


@insta485.app.route('/accounts/edit/')
def show_edit():
    """Display /accounts/edit route."""
    if 'username' not in flask.session:
        return flask.redirect(url_for('show_login'))

    logname = flask.session['username']
    connection = insta485.model.get_db()
    cursor = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ?",
            (logname,)
        )
    filename = cursor.fetchone()['filename']
    content = {'logname': logname, 'filename': filename}
    return flask.render_template("edit.html", **content)


@insta485.app.route('/accounts/password/')
def show_password():
    """Display /accounts/password route."""
    if 'username' not in flask.session:
        return flask.redirect(url_for('show_login'))
    logname = flask.session['username']
    content = {'logname': logname}
    return flask.render_template("password.html", **content)


def check_empty(strings):
    """
    Check whether at least one string in the list is empty.

    If at least one is empty, abort(400).
    """
    for string in strings:
        if string == '':  # don't use None!
            abort(400)


def compute_basename(filename):
    """
    Compute base name (filename without directory).

    We use a UUID to avoid clashes with existing files, and
    ensure that the name is compatible with the filesystem.
    """
    # uuid have 5 versions, 4 means don't accept argument
    stem = uuid.uuid4().hex
    suffix = pathlib.Path(filename).suffix  # get suffix, such as .jpg
    uuid_basename = f"{stem}{suffix}"
    return uuid_basename


def hash_password(password, algorithm='sha512'):
    """
    Hash the password using the given algorithm and a random salt.

    A password entry in the database contains the algorithm, salt
    and password hash separated by $.
    """
    # a new salt each time, e.g. 7a342958289b4b8595b5ffc249b85c36
    salt = uuid.uuid4().hex
    password_salted = salt + password
    # apply hash
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(password_salted.encode('utf-8'))
    password_hashed = hash_obj.hexdigest()
    # $ is used to separate
    password_db_string = "$".join([algorithm, salt, password_hashed])
    return password_db_string


def recover_password(password_hashed, password):
    """
    Verify whether the input password matches that in the database.

    Use password_hashed to get the algorithm and salt, then add salt with
    the input password and compare two hashed passwords.
    """
    algorithm = password_hashed.split('$')[0]
    salt = password_hashed.split('$')[1]
    password_hashed_true = password_hashed.split('$')[2]

    password_salted = salt + password
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(password_salted.encode('utf-8'))
    password_hashed = hash_obj.hexdigest()

    if password_hashed == password_hashed_true:
        return True
    return False


class Handler:
    """Handler for various operations."""

    @staticmethod
    def handle_login(connection):
        """Handle the login operation."""
        username = flask.request.form['username']
        password = flask.request.form['password']
        check_empty([username, password])
        cursor = connection.execute(
            "SELECT password "
            "FROM users "
            "WHERE username = ?",  # * no need for two '='
            (username, )
        )
        password_true_hashed = cursor.fetchone()
        if password_true_hashed is None:
            abort(403)  # no such username

        # username and password authentication
        password_true_hashed = password_true_hashed['password']
        if recover_password(password_true_hashed, password) is False:
            abort(403)   # password unmatched with database
        # * store minimum, don't store password
        flask.session['username'] = username

    @staticmethod
    def handle_create(connection):
        """Handle the create operation."""
        username = flask.request.form['username']
        password = flask.request.form['password']
        fullname = flask.request.form['fullname']
        email = flask.request.form['email']
        fileobj = flask.request.files["file"]
        filename = fileobj.filename
        check_empty([username, password, fullname, email, filename])

        cursor = connection.execute(
            "SELECT username "
            "FROM users "
            "WHERE username == ?",
            (username, )
        )
        if cursor.fetchone() is not None:  # if already exists, abort
            abort(409)

        # Handling the file
        uuid_basename = compute_basename(filename)
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        fileobj.save(path)

        # store into database
        password_hashed = hash_password(password)
        cursor = connection.execute(
            "INSERT INTO users"
            "(username, fullname, email, 'filename', 'password') "
            "VALUES "
            "(?, ?, ?, ?, ?)",
            (username, fullname, email, uuid_basename, password_hashed)
        )

        flask.session['username'] = username  # log in the user

    @staticmethod
    def handle_delete(connection):
        """Handle the delete operation."""
        if 'username' not in flask.session:
            flask.abort(403)
        logname = flask.session['username']
        # delete the old file for user
        cursor = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ?",
            (logname,)
        )
        uuid_basename = cursor.fetchone()['filename']
        path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
        os.remove(path)
        # delete the old file for posts
        cursor = connection.execute(
            "SELECT filename "
            "FROM posts "
            "WHERE owner = ?",
            (logname,)
        )

        uuid_basenames = cursor.fetchall()
        for i, uuid_basename in enumerate(uuid_basenames):
            uuid_bas = uuid_basename['filename']
            path = insta485.app.config["UPLOAD_FOLDER"]/uuid_bas
            os.remove(path)
            cursor = i
        # delete the user
        cursor = connection.execute(
            "DELETE FROM users WHERE username = ?",
            (logname,)
        )
        # delete the posts
        connection.execute("DELETE FROM posts WHERE owner = ? ", (logname, ))
        # clear the session
        flask.session.clear()

    @staticmethod
    def handle_edit(connection):
        """Handle the edit_account operation."""
        logname = flask.session['username']
        fullname = flask.request.form['fullname']
        email = flask.request.form['email']
        fileobj = flask.request.files["file"]
        filename = fileobj.filename  # not mandatory
        check_empty([fullname, email])

        cursor = connection.execute(
            "UPDATE users "
            "SET fullname = ?, email = ? "
            "WHERE username = ?",
            (fullname, email, logname)
        )

        if filename != '':  # there is a new photo
            # save the new file
            uuid_basename = compute_basename(filename)
            path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
            fileobj.save(path)
            # update the database
            cursor = connection.execute(
                "UPDATE users "
                "SET filename = ? "
                "WHERE username = ?",
                (uuid_basename, logname)
            )
            # delete the old file
            cursor = connection.execute(
                "SELECT filename "
                "FROM users "
                "WHERE username = ?",
                (logname,)
            )
            uuid_basename = cursor.fetchone()['filename']
            path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
            os.remove(path)

    @staticmethod
    def handle_update(connection):
        """Handle the update_password operation."""
        logname = flask.session['username']
        password = flask.request.form['password']
        new_password1 = flask.request.form['new_password1']
        new_password2 = flask.request.form['new_password2']
        check_empty([password, new_password1, new_password2])

        # check both new password match
        if new_password1 != new_password2:
            abort(401)

        # verify the password
        cursor = connection.execute(
            "SELECT password "
            "FROM users "
            "WHERE username = ?",
            (logname, )
        )
        # remember fetchone() returns a dict
        password_true_hashed = cursor.fetchone()['password']

        if recover_password(password_true_hashed, password) is False:
            abort(403)  # password unmatched with database

        # update the password
        new_password_hashed = hash_password(new_password1)
        cursor = connection.execute(
            "UPDATE users "
            "SET password = ? "
            "WHERE username = ?",
            (new_password_hashed, logname)
        )


@insta485.app.route('/accounts/', methods=['POST'])
def handle_accounts():
    """
    Handle all the operations.

    Operations include login, create, delete, edit_account
    and update_password operations for the account.
    """
    url = request.args.get('target')
    if url is None:
        url = '/'
    operation = flask.request.form['operation']

    # Connect to database
    connection = insta485.model.get_db()
    handler = Handler()
    if operation == 'login':
        handler.handle_login(connection)

    elif operation == 'create':
        if 'username' in flask.session:
            return flask.redirect(flask.url_for('show_edit'))
        handler.handle_create(connection)

    elif operation == 'delete':
        if 'username' not in flask.session:
            abort(403)  # not logged in
        handler.handle_delete(connection)

    elif operation == 'edit_account':
        if 'username' not in flask.session:
            abort(403)  # not logged in
        handler.handle_edit(connection)

    elif operation == 'update_password':
        if 'username' not in flask.session:
            abort(403)  # not logged in
        handler.handle_update(connection)

    else:
        raise ValueError("operation unrecognized")

    return flask.redirect(url)
