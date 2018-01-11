import logging
import json
import os
import tornado.ioloop
import tornado.web
import tornado.options

import gchart
import postgres


def env(name, default=None):
	return os.environ.get(name, default)


def debug_enabled():
	return env("DEBUG")


def path(folder):
	"""Gets abs path to static files"""
	path = os.path.realpath(__file__)
	directory = os.path.dirname(path)
	return u"{}/{}".format(directory, folder)


def configure_logger(name):
	logger = logging.getLogger(name)
	logger.addHandler(logging.StreamHandler())
	logger.setLevel(logging.DEBUG if debug_enabled() else logging.INFO)
	return logger


logger = configure_logger("tornado.application")


class Index(tornado.web.RequestHandler):

	def get(self, name="index.html"):

		logger.debug("rendering {}".format(name))
		suffix = name.split(".")[-1]
		content_type = "text/plain"
		if suffix == 'js':
			content_type = "application/javascript"
		elif suffix == 'html':
			content_type = "text/html"

		self.set_header("Content-Type", content_type)

		try:
			self.render(name)
		except IOError:
			self.set_status(404)


class BaseHandler(tornado.web.RequestHandler):

	def initialize(self):
		self.args = None

	def set_json_header(self):
		self.set_header("Content-type", "application/json")

	def write_json(self, obj, serializer=lambda obj: obj.isoformat()):
		self.set_json_header()
		self.write(json.dumps(obj, default=serializer))

	def get_args(self):
		"""Returns arguments to handler, regardless of format.

		Parses args from json if json request, gets them from `get_argument` otherwise.
		Does some filtering, trimming and general cleanup on args.
		args cached in request variable .args to avoid re-parsing args
		"""
		try:
			if self.args is not None:
				return self.args
		except AttributeError:
			pass

		args = {}
		body = self.request.body
		if self._is_json_request() and body:
			try:
				try:
					args = tornado.escape.json_decode(body)
				except UnicodeDecodeError:
					args = tornado.escape.json_decode(body.decode("ascii", "ignore"))
			except ValueError:
				pass
		else:
			args = {name: self.get_argument(name) for name in self.request.arguments.keys()}

		# Trim all input of leading and trailing spaces for all string values and force keys to strings
		args = dict([(str(key), value.strip() if isinstance(value, basestring) else value) for (key, value) in args.items()])

		self.args = args
		return args

	def _is_json_request(self):
		"""True iff a request has the json content header, Accept header or format=json GET arg"""
		headers = self._get_headers()
		return self.get_argument('format', None) == 'json' or \
			headers.get('Content-Type', '').find('/json') > -1 or \
			headers.get('Accept', '').find('/json') > -1

	def _get_headers(self):
		"""Gets headers for request without raising AttributeError if no headers set"""
		headers = {}
		try:
			headers = self.request.headers
		except AttributeError:
			pass
		return headers


class WithRedshiftConnection(BaseHandler):

	def initialize(self):

		self.args = None
		logger.debug("connecting to postgres")
		self.pg = postgres.Postgres()

	def on_finish(self):

		logger.debug("finishing pg request")
		self.pg.close()

	def write_datatable(self, columns, rows):
		charted = gchart.datatable(columns, rows)
		self.write_json(charted, serializer=gchart.serializer)


class Tables(WithRedshiftConnection):

	def get(self):
		rows = []
		for schema, tables in self.pg.get_schema_dict().items():
			for table in tables:
				rows.append((schema, table,))

		self.write_datatable([("Schema", "string"), ("Table", "string")], rows)


class Events(WithRedshiftConnection):

	def get(self, schema=None, table_name=None):
		args = self.get_args()
		event_limit = args.get('limit', 10)
		days = args.get('days')
		logger.debug("getting table")
		table = self.pg.get_table(table_name, table_schema=schema)
		logger.debug("table found")
		events = []
		if days:
			events, _ = table.sample(limit=0, days_old=days)
		else:
			events, _ = table.sample(limit=event_limit)
		logger.debug("{} events received".format(len(events)))
		if events:
			first_event = events[0]
			columns = gchart.detect_types(first_event.keys(), first_event.values())
			self.write_datatable(columns, [row.values() for row in events])
			logger.debug("events written")
		else:
			self.write_json({})


class DashboardStore(object):
	folder = path("./dashboards/")

	def list(self):
		return [path.split('/')[-1].split('.')[0] for path in os.listdir(self.folder) if path[-4:] == 'json']

	def get(self, name):
		f = self._open(name)
		data = f.read()
		f.close()
		return data

	def update(self, name, data):
		f = self._open(name, 'w')
		f.write(json.dumps(data, indent=2, default=lambda o: o.isoformat()))
		f.flush()
		f.close()

	def remove(self, name):
		f = self._open(name)
		f.close()
		os.remove(f.path)

	def _open(self, name, mode='r'):
		f = open(os.path.join(self.folder, "{}.json".format(name)), mode)
		return f


store = DashboardStore()


class Dashboards(BaseHandler):
	def get(self, name=None):
		out = []
		if not name:
			out = store.list()
		else:
			try:
				out = store.get(name)
			except IOError:
				self.set_status(404)
		self.set_json_header()
		self.write(out)

	def _do_update(self, name):
		args = self.get_args()
		data = args.get('data')
		logger.debug("updating {} with {}".format(name, data))
		if not data:
			self.set_status(400)
			data = {"error": "data field not set"}
		else:
			store.update(name, data)
		self.write_json(data)

	def put(self, name):
		self._do_update(name)

	def post(self, name):
		self._do_update(name)

	def delete(self, name):
		store.remove(name)


if __name__ == '__main__':
	HANDLERS = [
		(r'/?', Index),
		(r'/(?P<name>[-_\w]+\.\w+)$', Index),
		(r'/tables/', Tables),
		(r'/dashboards/', Dashboards),
		(r'/dashboards/(?P<name>[-_\w]+)/$', Dashboards),
		(r'/events/(?P<schema>[_\w]+)/(?P<table_name>[_\w]+)/', Events),
	]

	application = tornado.web.Application(HANDLERS, **{
		'debug': debug_enabled(),
		'template_path': path("static"),
	})
	port = 6080

	application.listen(port, **{
		'xheaders': True
	})

	tornado.options.parse_command_line()
	logger.debug("starting on {}".format(port))
	tornado.ioloop.IOLoop.instance().start()
