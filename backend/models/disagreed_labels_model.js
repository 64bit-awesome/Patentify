const { Schema, model } = require("mongoose");

const disagreedLabelsSchema = new Schema(
    {
        userIds:{ type: [Schema.Types.ObjectId] },
        document:{ type:String},
        mal:{type:String},
        hdw:{type:String},
        evo:{type:String},
        spc:{type:String},
        vis:{type:String},
        nlp:{type:String},
        pln:{type:String},
        kpr:{type:String}
    }, 
    {
        timestamps: true
    }
);

module.exports = model("disagreed_labels", disagreedLabelsSchema);