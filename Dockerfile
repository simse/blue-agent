FROM python:3.6-buster

RUN pip install -r requirements.txt

ENTRYPOINT ["python blueagent.py"]