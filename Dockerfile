FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./utils ./utils

CMD [ "streamlit", "run", "app.py" ]

EXPOSE 8501