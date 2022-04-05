import React from 'react';
import PropTypes from 'prop-types';

function LikeButton(props) {
  // def handle like and unlike
  let buttonText;
  let method;
  const { url, lognameLikesThis, updateFn } = props;
  if (lognameLikesThis === true) {
    buttonText = 'unlike';
    method = 'DELETE';
  } else {
    buttonText = 'like';
    method = 'POST';
  }

  return (
    <button
      type="button"
      className="like-unlike-button btn btn-primary mb-3"
      onClick={() => {
        // console.log(props.url, method);
        fetch(
          url,
          {
            credentials: 'same-origin',
            method, // method: method
          },
        )
          .then((response) => {
            if (!response.ok) throw Error(response.statusText);
          })
          .then(updateFn)
          .catch((error) => console.log(error));
      }}
    >
      {buttonText}
    </button>
  );
}

LikeButton.propTypes = {
  url: PropTypes.string.isRequired,
  lognameLikesThis: PropTypes.bool.isRequired,
  updateFn: PropTypes.func.isRequired,
};

export default LikeButton;
