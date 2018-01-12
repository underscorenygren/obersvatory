import datetime
import json
import os
import time
import pytz
from postgres import Postgres, logger
import pystache


def dump(obj):
	return json.dumps(obj, indent=2, default=lambda o: str(o))


def do_generate():
	pg = Postgres()
	schemas_filter = []

	output_folder = os.environ.get("OUTPUT_FOLDER", "static/")
	template_name = os.environ.get("TEMPLATE_SRC", "template.md")

	if not os.path.isdir(output_folder):
		logger.error("Path {} is not a directory, cannot continue".format(output_folder))
		return

	if not os.path.exists(template_name):
		logger.error("template {} doesn't exist, cannot continue".format(template_name))
		return

	schema_dict = pg.get_schema_dict()
	DEV = '_dev'
	PROD = ''
	schemas = {
			PROD: [],
			DEV: []
	}
	started_at = time.time()

	for schema_name in sorted(schema_dict):
		tables = schema_dict[schema_name]
		if not schemas_filter or schema_name in schemas_filter:
			schema = {"schema_name": schema_name, "schema_name_anchor": schema_name.lower()}
			events = []
			logger.debug("generating schema {}".format(schema_name))
			for table_name in sorted(tables):
				logger.debug("building event data for {}".format(table_name))
				table = pg.get_table(table_name, schema_name, validate=False)
				properties = sorted(table.get_properties())
				sample_event, event_text = table.sample(most_recent=True)
				if not event_text:
					event_text = table_name
				logger.debug("finished sampling")
				events.append({
					"event_text": event_text,
					"event_name": table_name,
					"event_anchor": (event_text or '').replace(" ", "-").lower(),
					"properties": [{"name": prop} for prop in properties],
					"sample_event": dump(sample_event),
				})
			schema["events"] = events
			if schema_name[-4:] == DEV:
				schemas[DEV].append(schema)
			else:
				schemas[PROD].append(schema)
	pg.close()

	for suffix, _schemas in schemas.items():
		out_name = os.path.join(output_folder, "events{}.md".format(suffix))
		with open(out_name, 'w') as f:
			with open(template_name, 'r') as _template:
				template = _template.read()

				logger.info("writing template({}) to {}".format(template_name, out_name))
				out = {
					"finished_in": round(time.time() - started_at, 2),
					"schemas": _schemas,
					"generated_at": str(
							datetime.datetime.now(pytz.utc)
							.astimezone(pytz.timezone("US/Eastern"))
						).split(".")[0]
					}
				logger.debug(dump(out))
				md = pystache.render(template, out)
				f.write(md)


def daemon(wait_minutes):
	while True:
		do_generate()
		logger.info("sleeping {} minutes".format(wait_minutes))
		time.sleep(wait_minutes * 60)


if __name__ == "__main__":
	import argparse

	parser = argparse.ArgumentParser("Generates markdown docs from events defined in redshift")
	parser.add_argument('--daemon', '-d', action="store_true",
		help="Runs the generation continously")
	parser.add_argument('--wait-minutes', type=float, default=60,
			help="the number of times to wait between runs")

	args = parser.parse_args()

	if args.daemon:
		logger.info("starting in daemon mode")
		daemon(args.wait_minutes)
	else:
		do_generate()
