FROM python:2.7.13

RUN mkdir -p /opt/app
WORKDIR /opt/app/
RUN mkdir charts
RUN mkdir dashboards

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./static ./static/
COPY *.py ./

ENV PG_HOST ""
ENV PG_PWD ""
ENV PG_DB ""
ENV PG_USER ""
ENV PG_PORT ""
ENV DEBUG ""
ENV STORE_ROOT ""
ENV PORT "80"
ENV AWS_ACCESS_KEY_ID ""
ENV AWS_SECRET_ACCESS_KEY ""
ENV S3_BUCKET ""
ENV MARKDOWN_FOLDER ""

ENTRYPOINT ["python"]
CMD ["main.py"]
