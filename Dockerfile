FROM python:3.6-buster

RUN pip install -r requirements.txt

EXPOSE 80

ENTRYPOINT ["python blueagent.py"]