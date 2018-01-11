FROM python:2.7.13

RUN mkdir -p /opt/app
WORKDIR /opt/app/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY template.md .
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

ENTRYPOINT ["python"]
CMD ["main.py"]
