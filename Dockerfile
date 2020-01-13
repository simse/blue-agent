FROM python:3.6-buster
LABEL author="Simon Sorensen (hello@simse.io)"

COPY . /app/walsingham
WORKDIR /app/walsingham

RUN pip install -r requirements.txt

EXPOSE 80
ENV DATABASE_NAME walsingham
ENV WEB_PORT 80
ENV TIMBER_SOURCE_ID 31364
ENV TIMBER_API_KEY eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJodHRwczovL2FwaS50aW1iZXIuaW8vIiwiZXhwIjpudWxsLCJpYXQiOjE1Nzg5MTc4MDMsImlzcyI6Imh0dHBzOi8vYXBpLnRpbWJlci5pby9hcGlfa2V5cyIsInByb3ZpZGVyX2NsYWltcyI6eyJhcGlfa2V5X2lkIjo2MDQ0LCJ1c2VyX2lkIjoiYXBpX2tleXw2MDQ0In0sInN1YiI6ImFwaV9rZXl8NjA0NCJ9.I6_nMfM0SK9MaG31k6m7TzFfmIyjfyJsACrYT8Om1Zo

CMD ["python", "blueagent.py"]