import streamlit as st
import random
import time
import boto3
import pymongo
from utils import bedrock
from langchain_community.embeddings import BedrockEmbeddings
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
    array_field = [doc[field_name_to_be_vectorized] for doc in docs]

    # Join array elements into a string  
    llm_input_text = '\n \n'.join(str(elem) for elem in array_field)

    #utility 
    newline, bold, unbold = '\n', '\033[1m', '\033[0m'
    print(newline + bold + 'Given Input : ' +  unbold + newline + llm_input_text + newline )


    # #return [Document(page_content = d["page_content"], metadata = d["metadata"]) for d in docs]
    return llm_input_text

print("started...")
mongo_uri = aws_utils.get_secret("workshop/atlas_secret")
print("got credentials...")

# Connect to the MongoDB database
client = pymongo.MongoClient(mongo_uri)
print("connected to mongoDB...")
db = client["sample_mflix"]
collection = db["movies"]

# Streamed response emulator
def response_generator(query_string):
    res = mdb_query(client, query_string, 5)

    print("finished search...")

    bedrock = boto3.client('bedrock-runtime')

    # prompt = f"""Human: Create a single paragraph of a movie description based on the descriptions below. Add additional details if needed.  Rephrase as much as possible.
    prompt = f"""Human: Create a mashup script based on the descriptions below.  Create a single paragraph description.
    {res} 
    \n\nBot: Let me create the script for you...
    """
    print(f"constructed prompt: {prompt}")

    body = json.dumps({
    "inputText": prompt,
    })

    # invoke titan model
    response = bedrock.invoke_model(
    modelId="amazon.titan-text-express-v1",
    body=body
    )

    response_body = json.loads(response['body'].read())
    outputText = response_body["results"][0]['outputText']
    print(outputText)

    for word in outputText.split():
        yield word + " "
        time.sleep(0.05)


st.title("Simple chat")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Let's create a movie description:"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": "Let me create the script for you about: " + prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(prompt))
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})