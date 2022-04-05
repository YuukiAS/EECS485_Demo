import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import CommentForm from './commentForm';
import LikeButton from './likeButton';
import DeleteCommentButton from './deleteCommentButton';

function Post(props) {
  // def Display number of image and post owner of a single post
  const [comments, setComments] = useState([]); // array of objects
  const [created, setCreated] = useState(''); // not human-readable
  const [imgUrl, setImgUrl] = useState('');
  const [likes, setLikes] = useState({
    lognameLikesThis: false,
    numLikes: 0,
    url: '',
  });
  const [owner, setOwner] = useState('');
  const [ownerImgUrl, setOwnerImgUrl] = useState('');
  const [ownerShowUrl, setOwnerShowUrl] = useState('');
  const [postShowUrl, setPostShowUrl] = useState('');
  const [postid, setPostid] = useState(0);

  const convertTimeStamp = (timeStamp) => moment(timeStamp).fromNow();

  const [likesUrl, setLikesUrl] = useState('');
  const [likesText, setLikesText] = useState(null);
  const [commentPostUrl, setCommentPostUrl] = useState('');
  const [commentsText, setCommentsText] = useState(null);
  const [numUpdates, setNumUpdates] = useState(0); // def just for re-render

  const { url } = props; // we pass REST API through props

  // * useCallback() is used to avoid re-rendering function
  const update = useCallback(() => {
    setNumUpdates(numUpdates + 1);
    // console.log(`update1 ${numUpdates}`);
  }, [numUpdates]);

  useEffect(() => {
    // console.log("useEffect1")
    // * asynchornous
    fetch(url, { credentials: 'same-origin' })
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
        return response.json(); // convert to JSON
      })
      // use data (JSON) to setState
      .then((data) => {
        setComments(data.comments);
        setCreated(data.created);
        setImgUrl(data.imgUrl);
        setLikes(data.likes);
        setOwner(data.owner);
        setOwnerImgUrl(data.ownerImgUrl);
        setOwnerShowUrl(data.ownerShowUrl);
        setPostShowUrl(data.postShowUrl);
        setPostid(data.postid);
      })
      .catch((error) => console.log(error));
  }, [numUpdates, url]);

  useEffect(() => {
    // console.log(`useEffect2`);
    if (likes.lognameLikesThis === true) {
      setLikesUrl(likes.url);
    } else {
      setLikesUrl(`/api/v1/likes/?postid=${postid}`);
    }
    if (likes.numLikes === 1) {
      setLikesText(
        <p>
          {likes.numLikes}
          &nbsp;like
        </p>,
      );
    } else {
      setLikesText(
        <p>
          {likes.numLikes}
          &nbsp;likes
        </p>,
      );
    }

    setCommentPostUrl(`/api/v1/comments/?postid=${postid}`);
    if (comments.length > 0) {
      setCommentsText(comments.map((comment) => {
        let deleteButton = null;
        if (comment.lognameOwnsThis === true) {
          const commentDeleteUrl = `/api/v1/comments/${comment.commentid}/`;
          deleteButton = <DeleteCommentButton url={commentDeleteUrl} updateFn={update} />;
        }
        // * every element should have a unique key
        return (
          <div className="row" key={comment.commentid}>
            <div className="col-3">
              <a href={comment.ownerShowUrl} className="fw-bold text-body text-decoration-none">
                {comment.owner}
              </a>
            </div>
            <div className="col-6">
              <p>{comment.text}</p>
            </div>
            <div className="col-3">
              {deleteButton}
            </div>
          </div>
        );
      }));
    }
    // console.log(`${commentPostUrl}`)
  }, [comments, likes, postid, update]); // * should include all dependency

  return (
    // width: 30rem;
    <div className="post card mx-auto m-2" style={{ width: `${30}rem` }}>
      <div className="card-body row">
        <div className="col-5">
          <a href={ownerShowUrl} className="row fw-bold text-body text-decoration-none">
            <div className="col-5">
              <img src={ownerImgUrl} className="img-thumbnail" alt={owner} />
            </div>
            <div className="col-7 mt-3">
              {owner}
            </div>
          </a>
        </div>
        <div className="col-4 offset-3 mt-3">
          <a href={postShowUrl} className="text-secondary fw-bold text-decoration-none">
            {convertTimeStamp(created)}
          </a>
        </div>
      </div>

      <img src={imgUrl} className="card-img" alt="post-content" />

      <div className="card-body">
        {likesText}
        <LikeButton
          url={likesUrl}
          lognameLikesThis={likes.lognameLikesThis}
          updateFn={update}
        />
        {commentsText}
        <CommentForm
          url={commentPostUrl}
          updateFn={update}
        />
      </div>

    </div>
  );
}

//* make sure data is valid
Post.propTypes = {
  // def isRequired: must provide the data
  url: PropTypes.string.isRequired,
};

export default Post;
