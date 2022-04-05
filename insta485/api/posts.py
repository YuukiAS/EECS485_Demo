"""REST API for posts."""
import flask
import insta485
from insta485.api.comments import check_authentication


@insta485.app.route('/api/v1/posts/')
def get_post():
  connection = insta485.model.get_db()
  if flask.request.authorization is not None:
    logname = flask.request.authorization['username']
    password = flask.request.authorization['password']
    check_authentication(logname, password, connection)
  elif 'username' in flask.session:
    logname = flask.session['username']
  else:
    flask.abort(403)
  
  posts = None
  if flask.request.args.get('page'):
    size_target = int(flask.request.args.get('page'))
    posts = connection.execute(
      "SELECT postid "
      "FROM posts "
      "ORDER BY posts.postid "
      "LIMIT 10"
      "OFFSET ?",
      ((size_target - 1)*10, )
    ).fetchall()
  elif flask.request.args.get('postid_lte'):
    size_target = int(flask.request.args.get('postid_lte'))
    posts = connection.execute(
      "SELECT postid "
      "FROM posts "
      "WHERE postid >= ?",
      (size_target, )
    ).fetchall()
  else:  
    size_target = flask.request.args.get('size')
    if not size_target:
      size_target = 10
    posts = connection.execute(
      "SELECT postid "
      "FROM posts "
      "ORDER BY posts.postid "
      "LIMIT ?",
      (size_target, )
    ).fetchall()
  result_dict_list = []
  for post in posts:
    result_dict_list.append(
      {
        "postid": int(post["postid"]),
        "url": "/api/v1/posts/{}/".format(post["postid"])
      }
    )
  
  context = {
    "url": "/api/v1/posts/",
    "next": "",
    "results": result_dict_list
  }
  return flask.jsonify(**context)


@insta485.app.route('/api/v1/posts/<int:postid_url_slug>/')
def get_post_with_id(postid_url_slug):
    """Return post on postid.

    Example:
    {
      "created": "2017-09-28 04:33:28",
      "imgUrl": "/uploads/122a7d27ca1d7420a1072f695d9290fad4501a41.jpg",
      "owner": "awdeorio",
      "ownerImgUrl": "/uploads/e1a7c5c32973862ee15173b0259e3efdb6a391af.jpg",
      "ownerShowUrl": "/users/awdeorio/",
      "postShowUrl": "/posts/1/",
      "url": "/api/v1/posts/1/"
    }
    """

    connection = insta485.model.get_db()

    if flask.request.authorization is not None:
      logname = flask.request.authorization['username']
      password = flask.request.authorization['password']
      check_authentication(logname, password, connection)
    elif 'username' in flask.session:
      logname = flask.session['username']
    else:
      flask.abort(403)

    cursor = connection.execute(
      "SELECT filename, created, owner "
      "FROM posts "
      "WHERE postid == ?",
      (postid_url_slug, )
    )
    post = cursor.fetchall()

    context = {}
    if post is None:
      return flask.jsonify(**context)
    
    post = post[0]
    owner = connection.execute(
      "SELECT filename "
      "FROM users "
      "WHERE username == ?",
      (post["owner"],)
    ).fetchone()
    comments = connection.execute(
      "SELECT owner, commentid, text "
      "FROM comments "
      "WHERE postid == ?",
      (postid_url_slug,)
    ).fetchall()
    comment_dict_list = []
    for comment in comments:
      comment_dict_list.append(
        {
          "commentid": int(comment["commentid"]),
          "owner": comment["owner"],
          "lognameOwnsThis": logname == comment["owner"],
          "ownerShowUrl": "/users/{}/".format(comment["owner"]),
          "text": comment["text"],
          "url": "api/v1/comments/{}/".format(comment["commentid"])
        }
      )
    likes = connection.execute(
      "SELECT owner, likeid "
      "FROM likes "
      "WHERE postid == ?",
      (postid_url_slug,)
    ).fetchall()
    like_dict = {}
    like_dict["numLikes"] = len(likes)
    like_dict["lognameLikesThis"] = False
    like_dict["url"] = None
    for like in likes:
      if like["owner"] == logname:
        like_dict["lognameLikesThis"] = True
        like_dict["url"] = "/api/v1/likes/{}/".format(like["likeid"])
        break
      
    context["created"] = post["created"]
    context["imgUrl"] = "/uploads/{}".format(post["filename"])
    context["owner"] = post["owner"]
    context["ownerImgUrl"] = "/uploads/{}".format(owner["filename"])
    context["ownerShowUrl"] = "/users/{}".format(post["owner"])
    context["postShowUrl"] = "/posts/{}/".format(postid_url_slug)
    context["postid"] = int(postid_url_slug)
    context["url"] = flask.request.path  # fixme missing '/'
    context["likes"] = like_dict
    context["comments"] = comment_dict_list
    return flask.jsonify(**context)
