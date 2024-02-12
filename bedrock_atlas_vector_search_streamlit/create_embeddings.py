import boto3
import os
import pymongo
from utils import bedrock
from langchain.embeddings import BedrockEmbeddings

# defind the bedrock client
boto3_bedrock = bedrock.get_bedrock_client(
    region="us-east-1"
)
mongo_uri = os.environ.get('ATLAS_URI')
# Connect to the MongoDB database
client = pymongo.MongoClient(mongo_uri)
db = client["sample_mflix"]
collection = db["movies"]

embedding_model_id = "amazon.titan-embed-text-v1"

# Initiate the embedding
embeddings = BedrockEmbeddings(model_id=embedding_model_id, client=boto3_bedrock)


# Get the required documents in the collection
documents = collection.find({"year": {"$gt": 2014}})
vector_field_name = "eg_vector"
field_name_to_be_vectorized = "fullplot"
print("started processing...")
i = 0
# Loop over all documents and vectorize the collections for the selected field
for document in documents:

    i += 1
    query = {'_id': document['_id']}
    
    if field_name_to_be_vectorized in document and vector_field_name not in document:
        # generate embedding
        text_as_embeddings = embeddings.embed_documents([document["title"] + " "+document[field_name_to_be_vectorized]])
        # update the document in MongoDB Atlas
        update = {'$set': {vector_field_name :  text_as_embeddings[0]}}
        collection.update_one(query, update)

    if i % 5 == 0:
        print("processed: " + str(i) + " records")
    if i > 200:
        break
    
print("finished processing: " + str(i) + " records")

