import streamlit as st
import time
import boto3
from utils import bedrock
import json
from langchain_aws import AmazonKnowledgeBasesRetriever
import os


print("started...")

# initialize AmazonKnowledgeBaseRetriever
retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=os.environ.get("BEBROCK_KB_ID"),
    region_name="us-west-2",
    retrieval_config={
        "vectorSearchConfiguration": {
            "numberOfResults": 5,
            "overrideSearchType": "SEMANTIC",
        }
    },
)

# Streamed response emulator
def response_generator(query_string):
    res = retriever.invoke(query_string, region_name="us-west-2")

    print("finished search...")

    bedrock = boto3.client('bedrock-runtime', region_name="us-west-2")

    prompt = f"""Human: You are expert on best practices for managing MongoDB clusters.  
    {res} 
    \n\nBot: Let me answer your question ...
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
if prompt := st.chat_input("Type your query:"):
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