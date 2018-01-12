## Observatory

This project aims to make it easier to inspect events in redshift/postgres, imagine it like
a lightweight kibana for redshift event data.

It provides an interactive ui that automatically queries and displays events.

It uses Google Charts to visualize events, and provides ways to automatically
create simple graphs.

It also provides a way to generate documentation for events to markdown.

## Installation & Running

Create a `.env` file with settings for your setup. Your Postgres/redshift connection details most importantly.

Then, you can run the whole stack with docker compose:

`docker-compose up`

You can also run each program by hand:

`PG_HOST=XXX PG_PWD=YYY ... DEBUG=true python app/main.py`

## Web

A tornado web server and JQuery UI that serves up and graphs the event data. Depending on how you
run it You can access it at http://127.0.0.1:6080/index.html or http://your-local-docker-host:your-port/index.html

The UI supports viewing a sampling of events, filtered by days back in time. It will pull all events
down and build charts from them, so it won't scale well for large number of events.

You can use the buttons to build simple charts, split by zero or one field.

You can also aggregate charts into simple dashboards at `/dashboards.html`

## Gen

`generator.py` is a program to generate markdown files from your event data. By default, every hour it will
generate `events.md` and `events_dev.md`, the latter for any tables with `_dev` as their suffix. It's not
yet very configurable, but it's a simple enough script that you could easily adapt. PRs welcome.

These files can be viewed in the UI at `YOUR_HOST/docs.html` and `YOUR_HOST/devdocs.html` respectively.

## Kubernetes

The stack is well set up to slide into an existing k8s stack. Use the `kube.yaml` and `service.yaml` to
setup to your own need, and then proxy to behind some authentication lest your event data be publicly available to all.

## Credits

observatory icon by Bernar  Novalyi from the Noun Project

marked.js by chjj - https://github.com/chjj/marked
