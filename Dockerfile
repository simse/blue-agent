FROM python:3.6-buster
LABEL author="Simon Sorensen (hello@simse.io)"

COPY . /app/walsingham
WORKDIR /app/walsingham

RUN pip install -r requirements.txt

EXPOSE 80
ENV DATABASE_NAME walsingham
ENV WEB_PORT 80

CMD ["python", "blueagent.py"]