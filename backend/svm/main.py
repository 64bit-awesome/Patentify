from pymongo import MongoClient

from itertools import cycle
from functions import *
from time import time

# Configuration:
MIN_TRAINING_SIZE = 3
MIN_AUTO_SAVE_CYCLES = 10

# establish connection to the database
client = MongoClient("mongodb://localhost:27017/PatentData")
db = client['PatentData']       
cluster = db['labels']

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

#create learner and check for base_learner
learner = None
try:
    print("Checking for base model...")
    base_estimator = model_loader()
    print("Base model successfully loaded.")
except FileNotFoundError:
    print("Base model not found, creating a new base model...")
    base_model_creator(client, stopwords)
    base_estimator = model_loader()
    print('Base model successfully created.')

if learner is None:
    learner = ActiveLearner(
        estimator=base_estimator,
        query_strategy=uncertainty_sampling
    )

# check if we need to find new uncertain patents:
if (uncertain_patents.count_documents({}) == 0):
    print('[INFO]: looking for new uncertain patents...')
    find_uncertain_patents(learner, client)

svm_metrics_init(learner, client) # init svm_metrics in database

# main logic loop: opens the stream and looks for updates to labels database, once it finds two distinct classes in target array (1 and 0),
# the svm model will train. Finally, it will dump the latest databse and resume token. Once the script is started up again, it will continue where
# it left off and not skip any patents that it missed while it was not running.

ids = [] #               document ids of newly annotated documents.
target = [] #            classification of newly annotated documents.
cycleCount = 1 #         number of training cycles completed by svm since launch.

entries = 0 #            stores the number of entries the model is going to be trained on.

try:
    db_stream = None
    continue_starter = None
    continue_after = None
    
    # load saved model into memory:
    try:
        continue_after = continue_starter = load('continue_token.joblib')
        db_stream = cluster.watch(resume_after=continue_starter)
        print('[INFO]: found resume token:', continue_starter)
    except FileNotFoundError:
        db_stream = cluster.watch()  
        continue_after = continue_starter = db_stream._resume_token
        print('[INFO]: no resume token found, using latest resume token:', continue_starter)

    # begin training model loop:  
    with db_stream as stream:
        print("Listening...")
        while stream.alive:
            change = stream.next()
            if change is not None:
                entries += 1

                entry = change['fullDocument']
                ids.append(entry['document'])
                print(f'Entry:{entry}')

                isAI = get_target(entry)
                target.append(isAI)

                # check target has multiple classes(1 and 0)
                if entries > MIN_TRAINING_SIZE and not (any(target) and all(target)):
                    continue_after = change['_id']
                    print(ids)
                    print(target)
                    X, y = svm_format(client, ids, target, stopwords)
                    learner.teach(X=X, y=y)
                    ids = []
                    target = []    

                    print("[INFO]: done with cycle", cycleCount)

                    if cycleCount % MIN_AUTO_SAVE_CYCLES == 0:
                        print(f'[AUTO-SAVE {time():0.0f}]: saved latest model and continue_token')
                        dump(learner.estimator, f'models/Final/auto-save_latest.joblib')
                        dump(continue_after,'continue_token.joblib')
                    
                    cycleCount += 1
except KeyboardInterrupt:
    print("[Interrupted]")

print("Finalizing...")
if continue_after is not continue_starter:
    dump(learner.estimator, f'models/Final/model_at_{time():0.0f}.joblib')
    dump(continue_after,'continue_token.joblib')
    print("[INFO]: dumped continue_after and model.")
else:
    print("No successful iterations... No changes will be made.")