const { Schema, model } = require("mongoose");

const patentSchema = new Schema(
  
  {
    documentId:{type:String, index: {unique: true, dropDups: true}},
    title:{type:String},
    claims:{ type: [String] },
    abstract:{type:String},
    date:{type:String},
    patentCorpus:{type:String}
  },

  { collection: "patents" }
);

module.exports = model("Patents", patentSchema);
