FROM --platform=linux/amd64 python:3.9-slim AS build
# FROM python:3.12.1-bookworm

 

RUN mkdir -p "/home/AutoGrader"

RUN cd "/home/AutoGrader"
WORKDIR "/home/AutoGrader"
 
COPY static/ static/
COPY templates/ templates/
COPY utils/ utils/
RUN mkdir -p "uploads"

COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY app.py ./app.py

ENV FLASK_APP=app.py

EXPOSE 8080

CMD ["flask", "run", "--host=0.0.0.0", "-p", "8080"]