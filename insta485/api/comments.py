"""REST API for comments."""
import flask
from flask import abort, request
from flask.helpers import make_response
import insta485
from insta485.views.accounts import recover_password


def check_authentication(username, password, db):
    """
    Verify whether username and password can authenticate a user.
    If they don't match, abort(403).
    """
    cursor = db.execute(
        "SELECT password "  # * must have whitespace!
        "FROM users "
        "WHERE username != ?",
        (username, )
    )
    password_hashed = cursor.fetchone()['password']
    # access control: if the user is not authenticated
    if recover_password(password_hashed, password) is False:
        abort(403)


@insta485.app.errorhandler(403)
def handle_forbidden(error):
    """Handle status code 403."""
    context = {
        "message": "Forbidden",
        "status_code": 403
    }
    return flask.jsonify(**context), 403


@insta485.app.errorhandler(404)
def handle_notFound(error):
    """Handle status code 404."""
    context = {
        "message": "Not found",
        "status_code": 404
    }
    return flask.jsonify(**context), 404


@insta485.app.route('/api/v1/comments/', methods=['POST'])
def post_comment():
    """
    Create a new comment based on the text in the JSON body
    for the specified post id.

    Example:
    {
        "commentid": 8,
        "lognameOwnsThis": true,
        "owner": "awdeorio",
        "ownerShowUrl": "/users/awdeorio/",
        "text": "Comment sent from httpie",
        "url": "/api/v1/comments/8/"
    }
    """
    postid = request.args.get('postid')  # * for ?..., don't use '<>'!
    text = request.json['text']
    # text = request.form.get('text')
    # connect to database
    connection = insta485.model.get_db()

    # access control
    if request.authorization is not None:
        logname = request.authorization['username']
        password = request.authorization['password']
        check_authentication(logname, password, connection)
    elif 'username' in flask.session:
        logname = flask.session['username']
    else:
        abort(403)

    # create the comment for the logged user
    connection.execute(
        "INSERT INTO comments(owner, postid, text) "
        "VALUES "
        "(?, ?, ?)",
        (logname, postid, text)
    )
    cursor = connection.execute(
        "SELECT last_insert_rowid() "
        "FROM comments "
    )
    commentid = cursor.fetchone()['last_insert_rowid()']

    context = {
        "commentid": commentid,
        "lognameOwnsThis": True,
        "owner": logname,
        "ownerShowUrl": "/users/{}/".format(logname),
        "text": text,
        "url": "/api/v1/comments/{}/".format(commentid)
    }
    return flask.jsonify(**context), 201  # use ** to expand dict


@insta485.app.route('/api/v1/comments/<commentid>/', methods=['DELETE'])
def delete_comment(commentid):
    """
    Delete the comment based on the comment id.
    """
    # connect to database
    connection = insta485.model.get_db()

    # access control
    if request.authorization is not None:
        logname = request.authorization['username']
        password = request.authorization['password']
        check_authentication(logname, password, connection)
    elif 'username' in flask.session:
        logname = flask.session['username']
    else:
        abort(403)

    # check the commentid exists and user own it
    cursor = connection.execute(
        "SELECT owner "
        "FROM comments "
        "WHERE commentid = ?",
        (commentid,)
    )
    owner = cursor.fetchone()
    if owner is None:
        abort(404)
    elif owner['owner'] != logname:
        abort(403)

    # delete the comment
    connection.execute(
        "DELETE "
        "FROM comments "
        "WHERE commentid = ?",
        (commentid,)
    )

    return make_response('', 204)
