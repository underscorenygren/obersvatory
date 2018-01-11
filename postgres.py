import logging
import os
from collections import defaultdict
import psycopg2
import psycopg2.extras


def env(key, default=None):
	return os.environ.get(key, default)


logger = logging.getLogger("postgres")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG if env("DEBUG") else logging.INFO)


def connect_args():
	return {
			"dbname": env("PG_DB", "dev"),
			"password": env("PG_PWD"),
			"user": env("PG_USER", "root"),
			"host": env("PG_HOST"),
			"port": int(env("PG_PORT", 5439))
		}

def connect():
	conn = psycopg2.connect(**connect_args())
	cursor = conn.cursor()
	return conn, cursor


class Postgres(object):

	INTERNAL_TABLES = ['users', 'tracks', 'aliases', 'identifies', 'pages']

	def __init__(self):

		self.conn, self.cursor = connect()

	def close(self):
		self.cursor.close()
		self.conn.close()

	def get_schema_dict(self, filter_prefix=[]):
		"""Returns a dict keyed by the schemas with table
		names as values"""

		sql = "SELECT table_name, table_schema FROM information_schema.tables"
		logger.debug(sql)
		self.cursor.execute(sql)

		out = defaultdict(list)
		ignored_schemas = ["information_schema", "public"]
		for table_name, table_schema in self.cursor.fetchall():
			if table_schema.find("pg_") != 0 and table_schema not in ignored_schemas:
				if any([table_schema.find(_filter) == 0 for _filter in filter_prefix]):
					logger.debug("skipping {} b/c of schema filter".format(table_schema))
				elif table_name not in self.INTERNAL_TABLES:
					out[table_schema].append(table_name)
		return out

	def get_table_list(self, schema_filter=None):
		"""Gets all the tables of the schemas that
		match the schema filter, or all if no filter
		is set"""
		schemas_and_tables = self.get_schema_dict()
		out = set()
		for schema, tables in schemas_and_tables.items():
			if not schema_filter or schema.find(schema_filter) != -1:
				for table in tables:
					if table not in self.INTERNAL_TABLES:
						out.add(table)
		return list(out)

	def get_table(self, table_name, table_schema=None, validate=True):
		if validate:
			schemas = self.get_schema_dict()
			if not table_schema:
				matches = []
				for schema, tables in schemas.items():
					if table_name in tables:
						matches.append(schema)
				if len(matches) == 0:
					raise ValueError("Table '{}' not found".format(table_name))
				if len(matches) > 1:
					raise ValueError("Table name '{}' matches multiple schemas: {}".format(table_name, matches))
				table_schema = matches[0]
		elif not table_schema:
			raise ValueError("must provide schema name when not validating")

		return Table(
				table_name,
				table_schema,
				self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor))

class Table(object):

	DEFAULT_FIELDS = ["id", "received_at", "uuid",
			"context_library_version", "event", "original_timestamp",
			"sent_at", "timestamp", "user_id", "context_library_name",
			"event_text", "uuid_ts"]
	# filters out keys that have this value, or that contain a _ prefix to this value
	SENSITIVE_FIELDS = ['email', "ip"]

	def __init__(self, name, schema, cursor):
		self.name = name
		self.schema = schema
		self.cursor = cursor

	def _full_name(self):
		return "{}.{}".format(self.schema, self.name)

	def get_columns(self):

		sql = ("select column_name from INFORMATION_SCHEMA.COLUMNS "
						"where table_name = '{}' AND table_schema = '{}'").format(self.name, self.schema)

		logger.debug(sql)
		self.cursor.execute(sql)
		return [row[0] for row in self.cursor.fetchall()]

	def get_properties(self):
		return self.get_properties_from_columns(self.get_columns())

	def get_properties_from_columns(self, columns):
		return [col for col in columns if col not in self.DEFAULT_FIELDS]

	def sample(self, limit=1, days_old=None, most_recent=False, filter_columns=[], force_include_columns=[]):
		sql_cmd = ["select * from {}".format(self._full_name())]
		if days_old:
			sql_cmd.append("where received_at > (current_date - interval '%d days')" % int(days_old))
		if most_recent:
			sql_cmd.append("order by received_at DESC")
		if limit:
			sql_cmd.append("limit {}".format(limit))
		always_include = ["uuid", "received_at", "user_id"] + force_include_columns
		sql = " ".join(sql_cmd)
		logger.debug("executing {}".format(sql))
		self.cursor.execute(sql)
		out = []
		event_text = None
		for hit in self.cursor.fetchall():
			event = {}
			for key, value in hit.items():
				if (key not in self.DEFAULT_FIELDS and key not in filter_columns) or key in always_include:
					if key in self.SENSITIVE_FIELDS or any([key.find("_{}".format(subfield)) != -1 for subfield in self.SENSITIVE_FIELDS]):
						try:
							value = "REDACTED({})".format(len(value))
						except TypeError:
							value = "REDACTED"
					event[key] = value
				elif key == "event_text":
					event_text = value
			out.append(event)
		return out, event_text
