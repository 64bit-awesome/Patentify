# Requires: Python 3.7+ (dictionaries must maintain order)

from pymongo import MongoClient

from itertools import cycle
from time import time
from functions import *

import traceback

from configuration import *

# establish connection to the database
client = MongoClient("mongodb://localhost:27017/PatentData")
db = client['PatentData']

collectionsToWatch = [
    { 'db': 'PatentData', 'coll': 'labels' },
    { 'db': 'PatentData', 'coll': 'svm_command' },
    { 'db': 'PatentData', 'coll': 'agreed_labels' },
    { 'db': 'PatentData', 'coll': 'disagreed_labels' }
]

match_pipeline = [
    { '$match': { 'ns': { '$in': collectionsToWatch } } },
    { '$match': { 'operationType': { '$in': ['insert', 'update', '**replace**'] } } }
]

uncertain_patents = db['uncertain_patents']

# load stopwords
try:
    stopwords = []                          
    with open('stopwords.txt') as f:                
        lines = f.readlines()
        for line in lines:
            stopwords.append(line[:-1])             
except FileNotFoundError:
    print('stopwords.txt not found, seeting stopwords="english"')
    stopwords= "english"                                                    #this adds all the stop words from a stopwords text file

# load the working model from a file or create a new base model:
learner = None
try:
    print("Checking for base model...")
    learner = model_loader()
    print("Base model successfully loaded.")
except FileNotFoundError:
    print("Base model not found, creating a new base model...")
    base_model_creator(client, stopwords)
    learner = model_loader()
    print('Base model successfully created.')

svm_metrics_init(learner, client) # init svm_metrics in database

# check if we need to find new uncertain patents:
if (uncertain_patents.count_documents({}) == 0):
    print('[INFO]: looking for new uncertain patents...')
    find_uncertain_patents(learner, client)

# main logic loop: opens the stream and looks for updates to labels database, once it finds two distinct classes in target array (1 and 0),
# the svm model will train. Finally, it will dump the latest databse and resume token. Once the script is started up again, it will continue where
# it left off and not skip any patents that it missed while it was not running.

cycleCount = 1 #         number of training cycles completed by svm since launch.
annotations = {} #       dictionary to store all annotations until they are trained on (this will keep only the latest).

entries = 0 #            stores the number of entries the model is going to be trained on.
try:
    db_stream = None
    continue_starter = None
    continue_after = None
    
    # load saved model into memory:
    try:
        continue_after = continue_starter = load('continue_token.joblib')
        db_stream = db.watch(match_pipeline, resume_after=continue_starter)
        print('[INFO]: found resume token:', continue_starter)
    except FileNotFoundError:
        db_stream = db.watch(match_pipeline)  
        continue_after = continue_starter = db_stream._resume_token
        print('[INFO]: no resume token found, using latest resume token:', continue_after)

    # begin training model loop:  
    with db_stream as stream:
        print("Listening...")
        while stream.alive:
            change = stream.next()
            if change is not None:               
                collection = change['ns']['coll'] # collection updated

                if collection == 'svm_command' and change['operationType'] == 'update':
                    handle_command(client, learner, change)
                
                # process labels which only have an annotation by one person:
                if collection == 'labels':
                    entries += 1
                    entry = change['fullDocument']

                    # if patent has been assigned, let's wait for a consensus:
                    assigned = db.patent_assignments.find_one({ 'assignments.documentId': entry['document'] })
                    
                    if(assigned == None):
                        isAI = get_target(entry)
                        annotations[entry['document']] = isAI
                    else:
                        print('[Active_Learning]: skipped', entry['document'], 'waiting on consensus')
                    

                # process labels which have been agreed by two annotators:
                if collection == 'agreed_labels':
                    if change['operationType'] == 'insert':
                        entry = change['fullDocument'] # the agreed labels entry
                        consensus = entry['consensus'] # the agreed upon label for the document
                        
                        # check if patent is from uncertain documents list:
                        removal = db.uncertain_patents.find_one_and_delete({ 'documentId': entry['document'] })
                        if removal != None:
                            print('[Active_Learning]: uncertain document annotated:', removal['documentId'])

                        # add to list of items to train on:
                        entries += 1

                        isAI = get_target(consensus)
                        annotations[entry['document']] = isAI
                                  
                
                # process labels which have been disagreed upon by two annotators (decided by 3rd):
                if collection == 'disagreed_labels':
                    if change['operationType'] == 'update':
                        documentId = db.disagreed_labels.find_one({ "_id": change['documentKey']['_id'] })['document']

                        # check if patent is from uncertain documents list:
                        removal = db.uncertain_patents.find_one_and_delete({ 'documentId': documentId })
                        if removal != None:
                            print('[Active_Learning]: uncertain document annotated:', removal['documentId'])

                        # train model on consensus:
                        consensus = change['updateDescription']['updatedFields']['consensus']

                        # add to list of items to train on:
                        entries += 1

                        isAI = get_target(consensus)
                        annotations[documentId] = isAI

                # check target has multiple classes(1 and 0)
                ids = list(annotations.keys()) #               document ids of newly annotated documents.
                target = list(annotations.values()) #            classification of newly annotated documents.

                if entries >= MIN_TRAINING_SIZE and not (any(target) and all(target)):
                    print(ids)
                    print(target)

                    X, y = svm_format(client, ids, target)
                    learner.teach(X=X, y=y)

                    entries = 0
                    annotations = {} # done with these annotations  

                    print("[INFO]: done with cycle", cycleCount)
                    continue_after = change['_id']

                    if cycleCount % MIN_AUTO_SAVE_CYCLES == 0:
                        print(f'[AUTO-SAVE {time():0.0f}]: saved latest model and continue_token')
                        dump(learner, f'models/working_model_[scikit-learn-{sklearn.__version__}].joblib')
                        dump(continue_after,'continue_token.joblib')

                    if cycleCount % F1_SCORE_INTERVAL == 0:
                        print('[SVM_Metrics]: new f1_score', )
                        # update uncertain f1_score
                        currentDateTime = datetime.utcnow()
                        
                        update_svm_metrics(client, {
                            "$push": {
                                "f1_scores": {
                                    "$each": [ { "score": calc_f1_score(learner, client), "date": currentDateTime } ],
                                    "$slice": -F1_SCORE_MAX # negative value returns last n elements
                                }
                            }
                        })
                    
                    cycleCount += 1


except KeyboardInterrupt:
    print("[Interrupted]")

# 'handle' exception and safely exit program:
except Exception as e:
    print(repr(e))
    print(traceback.format_exc())

print("Finalizing...")
if continue_after is not continue_starter:
    dump(learner, f'models/working_model_[scikit-learn-{sklearn.__version__}].joblib')
    dump(continue_after,'continue_token.joblib')
    print("[INFO]: dumped continue_after and model.")
else:
    print("No successful iterations... No changes will be made.")
    dump(continue_after,'continue_token.joblib')

# let the admin know the service is offline:
update_svm_metrics(client, {
    "$set": {
        "model_filename": 'offline'
    }
})