FROM python:3.9-bullseye

ENV CONTAINER_HOME=/server
WORKDIR $CONTAINER_HOME

ADD ./deploy/requirement.txt .

RUN pip install --no-cache-dir -r requirement.txt

COPY . .

WORKDIR $CONTAINER_HOME
CMD ["python","app.py"]