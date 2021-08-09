import sqlite3 as db
import os

from imfsearch.constants import DB_FULLPATH

def dict_factory(cursor, row):
	if not cursor or not row: return False
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

def get_type(var):
	if not var: return False
	return str(type(var))[8:-2]

_colors = {
	'header': '\033[95m',
	'blue': '\033[94m',
	'cyan': '\033[96m',
	'green': '\033[92m',
	'yellow': '\033[93m',
	'red': '\033[91m',
	'default': '\033[0m',
	'bold': '\033[1m',
	'underline' : '\033[4m'
}

def connect_db(row_factory=None):
	if not os.path.isfile(DB_FULLPATH):
		return False
	conn = db.connect(DB_FULLPATH)
	if row_factory:
		conn.row_factory = row_factory
	return conn

def is_field_in_db(table, column = '*', field = '', value = ''):
	conn = connect_db(dict_factory)
	if not conn: return False
	cur = conn.execute(f'SELECT "{column}" from "{table}" WHERE {field} = "{value}"').fetchone()
	return cur and len(cur) > 0