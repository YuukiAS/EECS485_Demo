import React from 'react'; // "import" is ES6 feature, which is "require" in ES5
import ReactDOM from 'react-dom';
import Post from './components/post';

// This method is only called once
ReactDOM.render(
  // Insert the post component into the DOM
  // todo 10 posts   GET /api/v1/posts/
  <Post url="/api/v1/posts/1/" />, // pass url in props
  document.getElementById('reactEntry'),
);
