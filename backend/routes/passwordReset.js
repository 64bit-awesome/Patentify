const express = require("express");
const router = express.Router();

const mongoose = require("mongoose");
const db = mongoose.connection.db

const crypto = require("crypto");
const User = require("../models/User_model");
const Token = require("../models/token");
const sendEmail = require("../utils/sendEmail");

router.post("/", async (req, res) => {
    try {
        const user = await User.findOne({ email: req.body.email });
        if (user == null)
            return res.status(400).json({ error: 'User with given email does not exist.'});

        let token = await Token.find({ userId: user._id });
        if (!token) {
            token = await new Token({
                userId: user._id,
                token: crypto.randomBytes(32).toString("hex"),
            }).save();
        }

        const link = `http://localhost:3000/passwordReset/${user._id}/${token.token}`;
        await sendEmail(user.email, "Patentify Password Reset", link);

        res.send("password reset link sent to your email account");
    } catch (error) {
        res.send("An error occured");
        console.log(error);
    }
});

router.post("/:userId/:token", async (req, res) => {
    try {
        /*const schema = Joi.object({ password: Joi.string().required() });
        const { error } = schema.validate(req.body);
        if (error) return res.status(400).send(error.details[0].message);

        const user = await User.findById(req.params.userId);
        if (!user) return res.status(400).send("invalid link or expired");

        const token = await Token.findOne({
            userId: user._id,
            token: req.params.token,
        });
        if (!token) return res.status(400).send("Invalid link or expired");

        user.password = req.body.password;
        await user.save();
        await token.delete();

        res.send("password reset sucessfully.");*/
    } catch (error) {
        res.send("An error occured");
        console.log(error);
    }
});

module.exports = router;