# Efficient script to insert titles+abstracts and report missing patent information.
# Runtime: ~2 days with datasets > 2 million.

import pymongo
import pandas as pd

from pymongo import UpdateOne

# connect to database:
client = pymongo.MongoClient("mongodb://localhost:27017/PatentData")
db = client['PatentData']
dbPatents = db['patents']
dbLabels = db['labels']
print('Connected to database.')

# load PGPUB data from tsv file:
applications = pd.read_csv(
  'application.tsv',
  header = 0, # header at row 0
  sep = '\t',  # tab separated
  dtype = { 'document_number': str, 'invention_title': str, 'abstract': str } # let's make it's all strings
)
print('Loaded application.tsv into dataframe.')
print()

operations = []
applications.drop(['id', 'type', 'application_number','date', 'country', 'series_code', 'rule_47_flag', 'filename'], axis=1, inplace=True)
applications.rename(columns={'document_number': 'documentId', 'invention_title': 'title', 'invention_abstract': 'abstract' }, inplace=True)

# remove those not in database:
PGPUBs = [element['documentId'] for element in list(dbPatents.find({"patentCorpus": "PGPUB"}, {"_id": False, "documentId": 1}))]
filtered = applications[applications['documentId'].isin(PGPUBs)]

del applications

# build bulk operation:
for application in filtered.itertuples():
    operations.append(
        UpdateOne({ "documentId": application.documentId }, { 
            "$set": { 
                'title': application.title,
                'abstract': application.abstract
            } 
        })
    )

print('Updating PGPUB metadata...')
result = dbPatents.bulk_write(operations, ordered=False)
print('Matched', result.matched_count, 'PGPUBs.')
print('Updated', result.modified_count, 'PGPUBs.')
print()

# free up some space:
del operations
del filtered
del result
#del PGPUBs

operations = []

# load patent data from tsv file:
patents = pd.read_csv(
  'patent.tsv',
  header = 0, # header at row 0
  sep = '\t',  # tab separated
  dtype = { 'id': str, 'number': str, 'abstract': str } # mixed types, let's make it all strings
)
print('Loaded patent.tsv into dataframe.')
print()

patents.drop(['type', 'number','date', 'country', 'kind', 'num_claims', 'filename', 'withdrawn'], axis=1, inplace=True)
patents.rename(columns={'id': 'documentId'}, inplace=True)

# remove those not in database:
USPATs = [element['documentId'] for element in list(dbPatents.find({"patentCorpus": "USPAT"}, {"_id": False, "documentId": 1}))]
filtered = patents[patents['documentId'].isin(USPATs)]

del patents

# build bulk operation:
for patent in filtered.itertuples():
    operations.append(
        UpdateOne({ "documentId": patent.documentId }, { 
            "$set": { 
                'title': patent.title,
                'abstract': patent.abstract
            } 
        })
    )

print('Updating USPAT metadata...')
result = dbPatents.bulk_write(operations, ordered=False)
print('Matched', result.matched_count, 'USPATs.')
print('Updated', result.modified_count, 'USPATs.')
print()

# free up some space:
del operations
del filtered
del result

operations = []
labelOperations = []

# load patent crosswalk data from tsv file:
crosswalk = pd.read_csv(
  'granted_patent_crosswalk.tsv',
  header = 0, # header at row 0
  sep = '\t',  # tab separated
  dtype = { 'document_number': str, 'patent_number': str }
)
print('Loaded granted_patent_crosswalk.tsv into dataframe.')
print()

filtered = crosswalk[crosswalk['document_number'].isin(PGPUBs)]

# build bulk operation:
for application in filtered.itertuples():
    operations.append(
        UpdateOne({ "documentId": application.document_number }, { 
            "$set": { 
                'documentId': application.patent_number
            } 
        })
    )

    labelOperations.append(
        UpdateOne({ "document": application.document_number }, { 
            "$set": { 
                'document': application.patent_number
            } 
        })
    )

print('Upgrading granted PGPUBs to USPATs...')
result = dbPatents.bulk_write(operations, ordered=False)
result2 = dbLabels.bulk_write(labelOperations, ordered=False)
print('Matched', result.matched_count, 'PGPUBs to USPATs.')
print('Updated', result.modified_count, 'PGPUBs to USPATs.')
print('Matched', result2.matched_count, 'PGPUBs to USPATs labels.')
print('Updated', result2.modified_count, 'PGPUBs to USPATs labels.')
print()


# free up some space:
del labelOperations
del operations
del crosswalk
del result2
del result

missing = list(dbPatents.find({ "title" : { "$exists" : False } }))

with open('missing.txt', 'w') as f:
    f.write('Patents with missing metadata:\n')
    for item in missing:
        f.write("%s\n" % item)
        
print('Wrote missing PGPUBs and USPATs to missing.txt')
print()

print('Done.')