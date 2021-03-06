const express = require("express");
const router = express.Router();
const passport = require("../auth/passport/index");
const userconfirmed = require("../models/user_confirmed_model")
const User = require("../models/user_model");
const bcrypt = require('bcryptjs');

/* GET users listing. */

router.get("/", async function (req, res, next) {
  try {
    const users = await User.find();
    res.json(users);
  } catch (err) {
    res.json({ message: err });
  }
});

// Login Handle
router.post("/Login", function (req, res, next) {

  // Passport callback
  passport.authenticate("local-login", function (error, user, info) {

    if (error) {
      return res.status(500).json({
        message: error || "Oops something happened",
      });
    }
    
    // Persistent Login
    req.logIn(user, function(error){
      if(error) {
        return res.status(500).json({
          message: error || "Oops something happend"
        })
      }
      // Adds a property to object and lets us know that the user has been authenticated.
      user.isAuthenticated = true; 
  
      return res.json(user);

    });
    

  })(req, res, next);
});

// Signup Handle
router.post("/register", function (req, res, next) {

  // Passport callback
  passport.authenticate("local-signup", function (error, user, info) {
    
    if (error) {
      return res.status(400).send('Email already in use\nTry logging in or using different email');
    }

   // Persistent Login
   req.logIn(user, function(error){
    if(error) {
      return res.status(500).json({
        message: error || "Oops something happend"
      })
    }
    
    // Adds a property to object and lets us know that the user has been authenticated.
    user.isAuthenticated = true; 

    return res.json(user);
    
  });

    
  })(req, res, next);
});

router.post("/findUser", async function(req,res,next){
  const IDs = req.body.IDs
  let users = []
  let user;

  for(const id of IDs) {
    user = await User.find({_id: id}).catch((error) => {
      res.status(500).json({ error: error });
    });
    users.push(...user)
  }
  
  if(users.length > 0){
    res.status(200).json(users)
  }
  else{
    res.status(500).json({message:"error finding users of each queue"})
  }
})

router.get("/verify/:userId/:uniqueString", (req, res) => {
  let{userId, uniqueString} = req.params;
  userconfirmed.find({userId}).then((inserted) => {
    if(inserted.length > 0){  
      inserted.forEach((value) => {
        const hashedUniqueString = value.uniqueString;
        bcrypt.compare(uniqueString, hashedUniqueString).then(inserted => {  
          if(inserted){  
            User.updateOne({_id: userId}, {verified: true}).then(() => {  
              userconfirmed.deleteMany({userId}).then(() => {
                res.status(200).json({ status: "verified" })  
              }).catch((error) => {  
                console.log(error);
                res.status(500).json({ error: error })
              })
            }).catch((error) => {  
              console.log(error);
              res.status(500).json({ error: error })
            })
          }
          else {
            res.status(400).json({ error: "Invalid verification token." })
          }
        }).catch((error) => {  
          console.log(error);
          res.status(500).json({ error: error })
        })
      });
    }
    else {
      res.status(400).json({ error: "Invalid verification token." })
    }
  }).catch((error)=> {
    console.log(error);
    res.status(400).json({ error: error })
  })
});

router.post("/", async (req, res) => {
  try {
      const { error } = validate(req.body);
      if (error) return res.status(400).send(error.details[0].message);

      const user = await new User(req.body).save();

      res.send(user);
  } catch (error) {
      res.send("An error occured");
      console.log(error);
  }
});

module.exports = router;
