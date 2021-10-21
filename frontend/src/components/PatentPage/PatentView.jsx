import React, { useState, useEffect, Fragment } from "react";
import { useParams } from "react-router";
import PatentCard from "../PatentPage/PatentCard";
import PatentForm from "../PatentPage/PatentForm";


const PatentView = (props) => {

  // Patents is an object that contains the documentID and the Patent Corpus
  // SetPatents is used to set the state for patents

  const [patents, setPatents] = useState();
  const [error, setError] = useState();
  const params = useParams();
  


  async function fetchData() {
    try {
      
      // we are using fetch to call the backend endpoint that contains all 368 patents.
      const response = await fetch("/patents");

      const body = await response.json();
      // body is an object with the response 
      
      setPatents(

        // This sets the state of patents to be an object that contains only the documentID and Patent Corpus
        // we map throught the object to acxomplish this

        body.map((id) => {
          return { documentId: id.documentId, patentCorpus: id.patentCorpus };
        })
      );
    } catch (error) {}
  }

  async function searchBar(){
    try {
     // we are using fetch to call the backend endpoint that contains all 368 patents.
     const response = await fetch(`/patents/search/${params.ID}`);

     const body = await response.json();
     if(body.message){
       setPatents(undefined)
       setError(body.message)
     }else{
      setPatents(

        // This sets the state of patents to be an object that contains only the documentID and Patent Corpus
        // we map throught the object to acxomplish this
  
        body.map((id) => {
          return { documentId: id.documentId, patentCorpus: id.patentCorpus };
        })
      );

     }
  
     

    }catch(error){ }


  }

  useEffect(() => {
    if(params.ID){

      searchBar()
    }else{
      fetchData();
    }


  }, []);
  
  return (
    <div className="container-fluid mt-5">

    <div className="row">
      {error
      ? <div>{error}</div>
      :<Fragment><div className="col-sm-2 col-lg-6 col-md-6"><PatentCard patents={patents} /></div><div className="col-sm-2 col-lg-6 col-md-6"><PatentForm patents={patents}/></div></Fragment>

      }
      
    </div>

    </div>
  );
  
};

export default PatentView;
