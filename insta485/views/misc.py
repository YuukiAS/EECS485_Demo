"""
Insta485 miscellanous view.

URLs include:
/explore/ *
/posts/<postid_url_slug>/
/likes/?target=URL *
/comments/?target=URL *
/posts/?target=URL *
/following/?target=URL *
"""

import uuid
import pathlib
import os
import flask
from flask import abort, url_for
import insta485


# handle GET /explore/ RECHECK
@insta485.app.route('/explore/')
def show_explore():
    """Display /explore route."""
    # check whether the user is logged in
    if 'username' not in flask.session:
        flask.redirect(url_for('show_login'))

    # logname = flask.session['username']
    logname = flask.session.get('username')
    # logname = 'awdeorio'
    connection = insta485.model.get_db()

    notfollow = []
    cursor = connection.execute(
        "SELECT username "
        "FROM users "
        "WHERE username != ?",
        (logname, )
    )
    notfollow1 = cursor.fetchall()
    curson2 = connection.execute(
        "SELECT username2 AS username "
        "FROM following "
        "WHERE username1 = ?",
        (logname, )
    )
    notfollow2 = curson2.fetchall()
    # print(notfollow1)
    # print(notfollow2)
    for i in notfollow1:
        if i not in notfollow2:
            notfollow.append(i["username"])
    # print(notfollow)
    temp = ','.join('?' * len(notfollow))
    # use username to get url for img
    cursor = connection.execute(
        "SELECT username, filename "
        "FROM users "
        f"WHERE username IN ({temp}) "
        "ORDER BY username ", notfollow
    )
    notfollow_result = cursor.fetchall()

    context = {
        "not_following": notfollow_result,
        "url": flask.request.path,
        "logname": logname
    }
    # print(flask.request.path)
    return flask.render_template('explore.html', **context)


# for post.html page
@insta485.app.route('/posts/<postid_url_slug>/', methods=['GET'])
# def show_posts(postid_url_slug):
def show_psots(postid_url_slug):
    """Display /posts/<postid_url_slug> route."""
    # if not logged in
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    logname = flask.session.get('username')
    connection = insta485.model.get_db()
    cursor = connection.execute(
                                "SELECT filename, owner, "
                                "created, postid FROM posts WHERE postid = ? ",
                                (postid_url_slug, )
                                )
    post = cursor.fetchone()
    if not post:
        return abort(404)
    cursor = connection.execute(
                                "SELECT filename FROM users "
                                "WHERE username = ? ",
                                (post["owner"], )
                                )
    file = cursor.fetchone()['filename']

    cursor = connection.execute(
        "SELECT likeid FROM likes WHERE postid = ? ",
        (post["postid"],)
    )
    likes = cursor.fetchall()

    cursor = connection.execute(
                                "SELECT owner, text, commentid FROM comments "
                                "WHERE postid = ? ORDER BY created, postid ",
                                (post["postid"],)
                                )
    comment = cursor.fetchall()

    cursor = connection.execute(
        "SELECT likeid FROM likes WHERE postid = ? AND owner = ? ",
        (postid_url_slug, logname)
    )
    lognamepost = cursor.fetchall()

    post["image_url"] = file
    post["likes"] = len(likes)
    post["comments"] = comment
    post["lognamepost"] = bool(len(lognamepost))

    return flask.render_template("post.html", username=logname, **post)


@insta485.app.route('/likes/', methods=['POST'])
def handle_likes():
    """Handle like and unlike operations."""
    post_target = flask.request.args.get('target')
    # logname = flask.session['username']
    logname = flask.session.get('username')
    postid = flask.request.form.get('postid')
    operation = flask.request.form.get('operation')
    # logname = "awdeorio"
    # Connect to database
    connection = insta485.model.get_db()

    if operation == 'like':
        # error checking
        cursor = connection.execute(
            "SELECT * FROM likes WHERE postid = ? AND owner = ? ",
            (postid, logname)).fetchall()
        if len(cursor) != 0:
            abort(409)
        connection.execute(
            "INSERT INTO likes(owner, postid) "
            "VALUES (?, ?)",
            (logname, postid)
        )
    else:
        # error checking
        cursor = connection.execute(
            "SELECT * FROM likes WHERE postid = ? AND owner = ? ",
            (postid, logname)).fetchall()
        if len(cursor) == 0:
            abort(409)
        connection.execute(
            "DELETE FROM likes "
            "WHERE postid = ?"
            "AND owner = ?",
            (postid, logname)
        )
    return flask.redirect(post_target)


@insta485.app.route('/comments/', methods=['POST'])
def handle_comments():
    """Handle create or delete comment operations."""
    post_target = flask.request.args.get('target')
    if not post_target:
        post_target = '/'
    # username = flask.session['username']
    username = flask.session.get('username')
    # username = 'awdeorio'
    operation = flask.request.form.get('operation')
    text = flask.request.form.get('text')
    postid = flask.request.form.get('postid')
    commentid = flask.request.form.get('commentid')

    # Connect to database
    connection = insta485.model.get_db()

    if operation == 'create':
        # check empty comment
        if text == '':
            abort(400)
        else:
            connection.execute(
                "INSERT INTO comments(owner, postid, text) "
                "VALUES(?, ?, ?) ",
                (username, postid, text)
            )
    elif operation == 'delete':
        # error checking
        cursor = connection.execute(
            "SELECT * FROM comments "
            "WHERE commentid = ? AND owner = ? ",
            (commentid, username)
        ).fetchone()
        if not cursor:
            flask.abort(403)
        connection.execute(
                "DELETE FROM comments "
                "WHERE commentid = ? AND owner = ? ",
                (commentid, username)
            )
    # error checking
    if not post_target:
        return flask.redirect('/')
    return flask.redirect(post_target)


@insta485.app.route('/posts/', methods=['POST'])
def handle_posts():
    """Handle create or delete post commands."""
    operation = flask.request.form.get('operation')
    postid = flask.request.form.get('postid')
    post_target = flask.request.args.get('target')
    # username = flask.session['username']
    username = flask.session.get('username')
    # username = 'awdeorio'
    connection = insta485.model.get_db()

    if operation == 'create':
        if flask.request.files.get('file') == '':
            abort(400)
        else:
            # deal with UUID filenames
            # Unpack flask object
            fileobj = flask.request.files["file"]
            filename = fileobj.filename
            # Compute base name (filename without directory).
            # We use a UUID to avoid
            # clashes with existing files
            # and ensure that the name is compatible with the
            # filesystem.
            stem = uuid.uuid4().hex
            suffix = pathlib.Path(filename).suffix
            uuid_basename = f"{stem}{suffix}"
            # Save to disk
            path = insta485.app.config["UPLOAD_FOLDER"]/uuid_basename
            fileobj.save(path)

            # insert into the database
            connection.execute(
                "INSERT INTO posts (filename, owner) "
                "VALUES (?, ?)",
                (uuid_basename, username)
            )
    elif operation == 'delete':
        # error checking
        exist = connection.execute(
            "SELECT * FROM posts "
            "WHERE postid = ? "
            "AND owner = ? ",
            (postid, username)
        ).fetchone()
        if not exist:
            flask.abort(403)

        cursor = connection.execute(
            "SELECT filename FROM posts WHERE postid = ?",
            (postid, )
        ).fetchone()["filename"]
        # remove_cursor = cursor.fetchone()["filename"]
        remove_path = insta485.app.config["UPLOAD_FOLDER"]/cursor
        os.remove(remove_path)

        connection.execute(
            "DELETE FROM posts "
            "WHERE postid = ? ",
            (postid, )
        )

    if not post_target:
        return flask.redirect('/users/'+username+'/')
    return flask.redirect(post_target)


@insta485.app.route('/following/', methods=['POST'])
def handle_following():
    """Handle the follow command."""
    post_target = flask.request.args.get('target')
    if post_target is None:
        post_target = '/'
    operation = flask.request.form.get('operation')
    username1 = flask.session.get('username')
    username2 = flask.request.form.get('username')
    connection = insta485.model.get_db()

    # for error checking, extract data from the following
    cursor = connection.execute(
        "SELECT username1 "
        "FROM following "
        "WHERE username1 = ? AND username2 = ?",
        (username1, username2)
    ).fetchall()
    if operation == 'follow':

        # error checking
        if len(cursor) != 0:
            abort(409)

        connection.execute(
            "INSERT INTO following(username1, username2) "
            "VALUES (?, ?)",
            (username1, username2)
        )

    elif operation == 'unfollow':

        # error checking
        if len(cursor) == 0:
            abort(409)

        connection.execute(
            "DELETE FROM following "
            "WHERE username1 = ? AND username2 = ? ",
            (username1, username2)
        )

    return flask.redirect(post_target)
