import React, { useState } from 'react';
import PropTypes from 'prop-types';

function CommentForm(props) {
  const [text, setText] = useState('');
  const { url, updateFn } = props;

  const handleChange = (e) => {
    setText(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch(
      url,
      {
        credentials: 'same-origin',
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }), // text: text
      },
    )
      .then((response) => {
        if (!response.ok) throw Error(response.statusText);
      })
      .then(updateFn)
      .catch((error) => console.log(error));
    setText(''); // restore the input
  };

  return (
    <form
      className="comment-form my-2"
      onSubmit={handleSubmit}
    >
      <input
        type="text"
        value={text}
        className="form-control"
        placeholder="Enter your comment"
        onChange={handleChange}
        required
      />
    </form>
  );
}

CommentForm.propTypes = {
  url: PropTypes.string.isRequired,
  updateFn: PropTypes.func.isRequired,
};

export default CommentForm;
