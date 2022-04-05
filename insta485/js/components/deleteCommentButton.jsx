import React from 'react';
import PropTypes from 'prop-types';

function DeleteCommentButton(props) {
  const { url, updateFn } = props;

  return (
    <button
      type="button"
      className="delete-comment-button btn btn-warning"
      onClick={() => {
        fetch(
          url,
          {
            credentials: 'same-origin',
            method: 'DELETE',
          },
        )
          .then((response) => {
            if (!response.ok) throw Error(response.statusText);
          })
          .then(updateFn)
          .catch((error) => console.log(error));
      }}
    >
      Delete
    </button>
  );
}

DeleteCommentButton.propTypes = {
  url: PropTypes.string.isRequired,
  updateFn: PropTypes.func.isRequired,
};

export default DeleteCommentButton;
