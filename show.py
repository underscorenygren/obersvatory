import json
from postgres import Postgres
import pystache


def dump(obj):
	return json.dumps(obj, indent=2, default=lambda o: str(o))


def show(obj):
	print dump(obj)


if __name__ == "__main__":

	pg = Postgres()

	_all = pg.get_schema_dict()

	print "/** SCHEMAS **/"
	show(_all)

	_filter = "python_dev"
	tables = pg.get_table_list(schema_filter=_filter)

	print "/** Tables on filter={} **/".format(_filter)
	show(tables)

	name = "log_in"
	table = pg.get_table(name, "python")

	print "Columns for {}".format(name)
	columns = table.get_columns()
	show(columns)

	print "properties for {}".format(name)
	properties = table.get_properties_from_columns(columns)
	show(properties)

	print "Sample event for {}".format(name)
	events, event_text = table.sample(most_recent=True)
	show(events)

	with open("events.md", 'w') as f:
		with open('template.md', 'r') as _template:
			template = _template.read()

			md = pystache.render(template, {
				"event_text": event_text,
				"event_name": name,
				"properties": [{"name": _name} for _name in properties],
				"sample_event": dump(events[0])
			})

			f.write(md)

