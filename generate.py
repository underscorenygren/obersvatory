import datetime
import json
import pytz
from postgres import Postgres, logger
import pystache


def dump(obj):
	return json.dumps(obj, indent=2, default=lambda o: str(o))


if __name__ == "__main__":

	pg = Postgres()
	schemas_filter = []

	schema_dict = pg.get_schema_dict()
	DEV = '_dev'
	PROD = ''
	schemas = {
			PROD: [],
			DEV: []
	}

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
		out_name = "events{}.md".format(suffix)
		template_name = 'template.md'
		with open(out_name, 'w') as f:
			with open(template_name, 'r') as _template:
				template = _template.read()

				logger.info("writing template({}) to {}".format(template_name, out_name))
				out = {
					"schemas": _schemas,
					"generated_at": str(
							datetime.datetime.now(pytz.utc)
							.astimezone(pytz.timezone("US/Eastern"))
						).split(".")[0]
					}
				logger.debug(dump(out))
				md = pystache.render(template, out)
				f.write(md)
