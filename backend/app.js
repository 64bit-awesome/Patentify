require("dotenv").config();

const mongoose = require("mongoose");
const express = require('express');
const path = require('path');
const logger = require('morgan');
const passport = require('./auth/passport/index');

// Simple cookie-based session middleware.
const cookieSession = require('cookie-session');

// Routes
const usersRouter = require('./routes/users');
const patentsRouter = require('./routes/patents-api');
const passwordRouter = require('./routes/passwordReset');



const app = express();
app.listen(4000, 'localhost'); // SECURITY: only bind to localhost, should not be exposed to internet.

// Here we are connecting to our MongoDB database that is hosted on Compute1 at FIU
mongoose
  .connect(process.env.MONGO_URL, 
    { 
      reconnectTries: 60,
      reconnectInterval: 3000, // wait 3 seconds before attempting again
      useNewUrlParser: true, 
      useUnifiedTopology: true 
    })
  .then((x) =>
    console.log(`Connected to Mongo! Database name: "${x.connections[0].name}"`)
  )
  .catch((err) => console.error("Error connecting to mongo", err));

const app_name = require("./package.json").name;

const debug = require("debug")(
  `${app_name}:${path.basename(__filename).split(".")[0]}`
);


app.use(logger('dev'));
app.use(express.json());

// BodyParser
app.use(express.urlencoded({ extended: false }));

// This module stores the session data on the client within a cookie
app.use(cookieSession({
  name: 'session',
  keys: ['key1', 'key2'],
  maxAge: (new Date(253402300000000) - new Date()) / 1000 // set the cookie to never expire unless logged out.
}))

// Passport
app.use(passport.initialize());
app.use(passport.session());

// MiddleWare // Here is where we let our application use the route that has been created
app.use('/users', usersRouter);
app.use('/patents-api', patentsRouter);
app.use('/passwordReset', passwordRouter);


// catch 404 and forward to error handler
app.use(function(req, res, next) {
  next(createError(404));
});

// error handler
app.use(function(err, req, res, next) {
  // set locals, only providing error in development
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // render the error page
 res.status(err.status || 500);
 res.json({ error: err })
});

module.exports = app;
