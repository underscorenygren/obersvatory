import datetime
import decimal
import numbers


def serializer(obj):
	if isinstance(obj, (datetime.datetime, datetime.date)):
		return obj.strftime("Date(%Y, %m, %d, %H, %M, %S, %f)")

	elif isinstance(obj, decimal.Decimal):
		return float(obj)

	raise TypeError("Type %s not serializable" % type(obj))


def python_to_google_type(obj):
	if isinstance(obj, basestring):
		return "string"
	if isinstance(obj, datetime.date):
		# TODO separate date?
		return "datetime"
	if isinstance(obj, bool):
		return "boolean"
	if isinstance(obj, numbers.Number):
		return "number"

	return "string"


def detect_types(column_names, one_row):
	cols = []
	for i in range(0, len(column_names)):
		column_name = column_names[i]
		detected = python_to_google_type(one_row[i])
		cols.append((column_name, detected,))
	return cols


def datatable(columns, rows):
	"""Columns and rows are both arrays,
	the former of (name, type) tuples"""

	return {
			"cols": [{"label": key, "type": val} for (key, val) in columns],
			"rows": [
					{"c": [{"v": cell} for cell in row]} for row in rows]
			}
