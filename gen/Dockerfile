FROM python:2.7.13

RUN mkdir -p /opt/app/static
WORKDIR /opt/app/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY template.md .
COPY *.py ./

ENV PG_HOST ""
ENV PG_PWD ""
ENV PG_DB ""
ENV PG_USER ""
ENV PG_PORT ""
ENV DEBUG ""
ENV MARKDOWN_FOLDER ""

ENTRYPOINT ["python"]
CMD ["generate.py", "--daemon"]
