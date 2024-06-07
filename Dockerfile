FROM python:3

WORKDIR /usr/src/app

COPY ./bedrock_atlas_vector_search_streamlit/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt



COPY ./bedrock_atlas_vector_search_streamlit/app.py  ./app.py
COPY ./bedrock_atlas_vector_search_streamlit/utils ./utils


CMD [ "streamlit", "run", "app.py" ]

EXPOSE 8501