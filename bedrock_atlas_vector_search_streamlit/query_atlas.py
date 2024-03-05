import boto3
import os
import pymongo
from utils import bedrock
from langchain.embeddings import BedrockEmbeddings
from utils import aws_utils
import json

embedding_model_id = "amazon.titan-embed-text-v1"
boto3_bedrock = bedrock.get_bedrock_client()

# Initiate the embedding
embeddings = BedrockEmbeddings(model_id=embedding_model_id, client=boto3_bedrock)
field_name_to_be_vectorized = "fullplot"
vector_field_name = "eg_vector"
index_name = "default"
# filter the data using the criteria and do a schematic search
def mdb_query(mdbclient, query, kcount):
    text_as_embeddings = embeddings.embed_documents([query])
    embedding_value = text_as_embeddings[0]
    print("embedding size: " + str(len(embedding_value)))

    # get the vector search results based on the filter conditions.
    response = collection.aggregate([
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "eg_vector",
                "queryVector": text_as_embeddings[0],
                "numCandidates": 200,
                "limit": 4
            }
        }, {
            '$project': {
                'score': {'$meta': 'searchScore'}, 
                field_name_to_be_vectorized : 1,
                'title': 1,
                'claim_id' : 1,
                '_id':0
            }
        }
    ])

    # Result is a list of docs with the array fields
    docs = list(response)

    # Extract an array field from the docs
    array_field = [doc['title']+": "+doc[field_name_to_be_vectorized] for doc in docs]

    # Join array elements into a string  
    llm_input_text = '\n \n'.join(str(elem) for elem in array_field)

    #utility 
    newline, bold, unbold = '\n', '\033[1m', '\033[0m'
    print(newline + bold + 'Given Input : ' +  unbold + newline + llm_input_text + newline )


    # #return [Document(page_content = d["page_content"], metadata = d["metadata"]) for d in docs]
    return llm_input_text

print("started...")
# mongo_uri = os.environ.get('ATLAS_URI')
mongo_uri = aws_utils.get_secret("workshop/atlas_secret")
print("got credentials...")
# Connect to the MongoDB database
client = pymongo.MongoClient(mongo_uri)
print("connected to mongoDB...")
db = client["sample_mflix"]
collection = db["movies"]

# query_string = "traveling stars manual"
query_string = "traveling romantic story"

print("\n" + "Searching for: " + query_string + "\n")

res = mdb_query(client, query_string, 5)

print("finished search...")

print("Done!")