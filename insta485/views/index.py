"""
Insta485 index (main) view.

URLs include:
/
"""
import flask
from flask import abort
from flask.helpers import url_for, send_from_directory
import arrow
import insta485


@insta485.app.route('/')
def show_index():
    """Display / route."""
    if 'username' not in flask.session:
        return flask.redirect(url_for('show_login'))

    logname = flask.session.get('username')
    # logname="awdeorio"
    # Connect to database
    connection = insta485.model.get_db()

    # Fixed: don't show unfollowing people based on the logname
    followuser = []
    followuser.append(logname)
    cursor = connection.execute(
        "SELECT username2 "
        "FROM following "
        "WHERE username1 = ?",
        (logname, )
    )

    cursor_following = cursor.fetchall()
    for i in cursor_following:
        followuser.append(i["username2"])

    # users
    cursor = connection.execute(
        "SELECT username, fullname, filename "  # * must have whitespace!
        "FROM users "
        "WHERE username != ?",
        (logname, )
    )
    users = cursor.fetchall()  # get a list of the matching rows

    # posts
    temp = ','.join('?' * len(followuser))
    cursor = connection.execute(
        "SELECT postid, filename, created, owner "
        "FROM posts "
        f"WHERE owner IN ({temp}) "
        "ORDER BY created DESC, postid DESC ", followuser
    )
    posts = cursor.fetchall()

    for post in posts:
        # filename = post["filename"]
        # post["filename"] = insta485.app.config["UPLOAD_FOLDER"]/filename
        cursor = connection.execute(
            "SELECT comments.owner, comments.text "
            "FROM comments "
            "WHERE comments.postid == ?",
            (post["postid"], )
        )
        comments = cursor.fetchall()
        post["comments"] = comments
        cursor = connection.execute(
            "SELECT COUNT(*) "
            "FROM likes "
            "WHERE postid == ?",
            (post["postid"], )
        )
        likes = cursor.fetchall()
        post["likes"] = likes[0]['COUNT(*)']
        cursor = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE users.username == ?",
            (post["owner"], )
        )
        post["owner_img_url"] = cursor.fetchone()['filename']
        timestamp = arrow.get(post["created"], 'YYYY-MM-DD HH:mm:ss')
        post["created"] = timestamp.humanize()
        cursor = connection.execute(
            "SELECT EXISTS("
            "SELECT * FROM likes WHERE "
            "postid == ? "
            "AND owner== ?)",
            (post["postid"], logname)
        )
        val = cursor.fetchone()
        val = list(val.values())[0]
        if val == 1:
            post["is_liked"] = True
        else:
            post["is_liked"] = False
    context = {
        "logname": logname,
        "users": users,
        "posts": posts
    }  # Add database info to context
    return flask.render_template("index.html", **context)


@insta485.app.route('/uploads/<filename>')
def get_file(filename):
    """Return pictures in upload directory."""
    if 'username' not in flask.session:
        abort(403)
    return send_from_directory(insta485.app.config['UPLOAD_FOLDER'], filename)


@insta485.app.route('/static/css')
def get_css():
    """Return the css in static directory."""
    return send_from_directory(
        insta485.app.config['STATIC_FOLDER']/'css', 'style.css')


@insta485.app.route('/static/logo')
def get_logo():
    """Return the logo in static directory."""
    return send_from_directory(
        insta485.app.config['STATIC_FOLDER']/'images', 'logo.png')


@insta485.app.route('/', methods=['POST'])
def handle_index():
    """Handle like, unlike, comment of posts."""
    url = flask.request.args.get('target')
    if url is None:
        url = '/'
    operation = flask.request.form['operation']
    connection = insta485.model.get_db()
    # import pdb;pdb.set_trace()
    if operation == 'like':
        username = flask.session['username']
        postid = flask.request.form['postid']
        _ = connection.execute(
            "INSERT OR IGNORE INTO "
            "likes(owner, postid) "
            "VALUES (?, ?)",
            (username, postid)
        )
    elif operation == 'unlike':
        username = flask.session['username']
        postid = flask.request.form['postid']
        _ = connection.execute(
            "DELETE FROM likes "
            "WHERE owner == ? "
            "AND postid == ?",
            (username, postid)
        )

    elif operation == 'comment':
        username = flask.session['username']
        postid = flask.request.form['postid']
        text = flask.request.form['text']
        _ = connection.execute(
            "INSERT INTO comments(owner, postid, text) "
            "VALUES (?, ?, ?)",
            (username, postid, text)
        )

    return flask.redirect(flask.url_for('show_index'))
