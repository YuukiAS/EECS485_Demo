"""
Insta485 users view.

URLs include:
/users/<user_url_slug>/
/users/<user_url_slug>/followers/
/users/<user_url_slug>/following/
"""
import flask
import insta485


@insta485.app.route('/users/<user_url_slug>/', methods=['GET'])
def show_user(user_url_slug):
    """Display /users/<user_url_slug>/ route."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))
    # logname = flask.session['username']
    logname = flask.session.get('username')
    connection = insta485.model.get_db()

    user = connection.execute(
        "SELECT username, fullname, filename "
        " FROM users "
        "WHERE username == ?",
        (user_url_slug, )
    ).fetchone()

    if not user:
        flask.abort(404)

    cursor = connection.execute(
        "SELECT username2 "
        "FROM following "
        "WHERE username1 == ? "
        "AND username2 == ?",
        (logname, user["username"])
    )
    count = cursor.fetchall()
    logname_follows_username = bool(len(count) == 1)
    cursor = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username2 == ?",
        (user["username"], )
    )
    followers = cursor.fetchall()
    followers = followers[0]['COUNT(*)']
    cursor = connection.execute(
        "SELECT COUNT(*) "
        "FROM following "
        "WHERE username1 == ?",
        (user["username"], )
    )
    following = cursor.fetchall()
    following = following[0]['COUNT(*)']
    cursor = connection.execute(
        "SELECT postid, filename "
        "FROM posts "
        "WHERE posts.owner == ?",
        (user["username"], )
    )
    posts = cursor.fetchall()
    total_posts = len(posts)

    context = {
        "logname": logname,
        "target": user_url_slug,
        "total_posts": total_posts,
        "following": following,
        "followers": followers,
        "posts": posts,
        "user": user,
        "logname_follows_username": logname_follows_username
    }
    return flask.render_template("user.html", **context)


@insta485.app.route('/users/<user_url_slug>/followers/', methods=['GET'])
def show_followers(user_url_slug):
    """Display /users/<user_url_slug>/followers/ route."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))

    logname = flask.session['username']
    connection = insta485.model.get_db()
    user = connection.execute(
        "SELECT username, fullname, filename "
        " FROM users "
        "WHERE username == ?",
        (user_url_slug, )
    ).fetchone()
    if not user:
        flask.abort(404)

    cursor = connection.execute(
        "SELECT username1 AS username "
        "FROM following "
        "WHERE username2 == ?",
        (user_url_slug, )
    )
    followers = cursor.fetchall()

    cursor = connection.execute(
        "SELECT username2 "
        "AS username "
        "FROM following "
        "WHERE username1 == ?",
        (logname, )
    )
    my_foll = cursor.fetchall()
    for user in followers:
        if user in my_foll:
            user["logname_follows_username"] = True
        else:
            user["logname_follows_username"] = False
        cursor = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ?",
            (user['username'],)
        )
        user['filename'] = cursor.fetchone()['filename']

    context = {
        "logname": logname,
        "followers": followers,
        "current_username": user_url_slug
    }
    return flask.render_template("followers.html", **context)


@insta485.app.route('/users/<user_url_slug>/following/', methods=['GET'])
def show_following(user_url_slug):
    """Display /users/<user_url_slug>/following/ route."""
    if 'username' not in flask.session:
        return flask.redirect(flask.url_for('show_login'))

    logname = flask.session['username']
    connection = insta485.model.get_db()
    user = connection.execute(
        "SELECT username, fullname, filename "
        " FROM users "
        "WHERE username == ?",
        (user_url_slug, )
    ).fetchone()
    if not user:
        flask.abort(404)
    cursor = connection.execute(
        "SELECT username2 AS username "
        "FROM following "
        "WHERE username1 == ?",
        (user_url_slug, )
    )
    following = cursor.fetchall()
    cursor = connection.execute(
        "SELECT username2 AS username "
        "FROM following "
        "WHERE username1 == ?",
        (logname, )
    )
    mytemp = cursor.fetchall()
    for user in following:
        if user in mytemp:
            user["logname_follows_username"] = True
        else:
            user["logname_follows_username"] = False
        cursor = connection.execute(
            "SELECT filename "
            "FROM users "
            "WHERE username = ?",
            (user['username'],)
        )
        user['filename'] = cursor.fetchone()['filename']

    context = {
        "logname": logname,
        "following": following,
        "current_username": user_url_slug
    }
    return flask.render_template("following.html", **context)
