import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from utils import aws_utils

# Connect to MongoDB Atlas cluster
mongo_uri = aws_utils.get_secret("workshop/atlas_secret")
client = MongoClient(mongo_uri)
db = client["streamlit_demo"]
collection = db["tasks"]

# Streamlit app
st.title("Chatbot Application")

user = st.text_input("Enter your name:")

# Function to insert message to MongoDB
def insert_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {"user":user, "timestamp": timestamp, "message": message}
    collection.insert_one(data)

# Display existing chat messages from MongoDB
existing_messages = collection.find({"user":user}, {"_id": 0, "timestamp":1, "message": 1})
for message in existing_messages:
    if "message" in message:
      st.write(f"{message['timestamp']} - {message['message']}")
    else:
        st.write("No messages found.")

# Text input field for user to enter message
user_message = st.text_input("Enter your message:")

# Save button functionality to insert user message to MongoDB
if st.button("Send"):
    if user_message:
        insert_message(user_message)
        st.success("Message sent successfully!")
    else:
        st.error("Please enter a message.")

# Clear button functionality to clear the complete application and close it
if st.button("Clear"):
    st.session_state.clear()
    st.stop()