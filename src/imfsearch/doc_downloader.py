import sqlite3 as db
import os, time, glob

from imfsearch.drivers import chrome_driver
from imfsearch.constants import DB_FULLPATH, DOC_PATH
from imfsearch.helpers import dict_factory, get_type, printc, connect_db

driver = None

def check_downloads(doclist):
	completed = True
	conn = connect_db()
	for i in range(len(doclist)):
		doc = doclist[i]
		file_exists = os.path.isfile(doc['path'])
		filepath = doc['path'] if file_exists else ''
		q = '''UPDATE docs SET Filepath = ? WHERE "index" = ?'''
		conn.execute(q, (filepath, doc['index']))
		conn.commit()
		if not file_exists: completed = False
	conn.close()
	return completed

def delete_doc(filepath):
	if not get_type(filepath) == "str" or not os.path.isfile(filepath):
		return False
	os.remove(filepath)
	return True

def dl_doc(link, filename):
	global driver
	print('Downloading {0} from "{1}"...'.format(filename, link))
	driver.get(link)

def init(redownload=False):
	os.makedirs(DOC_PATH, exist_ok=True)
	q = "SELECT * FROM 'docs'" + ("" if redownload else " WHERE Filepath = ''")
	conn = connect_db(dict_factory)
	cur = conn.execute(q).fetchall()
	if not len(cur):
		post_check = True
	else:
		global driver
		driver = chrome_driver.install()
		doclist = []
		for i in range(len(cur)):
			row = cur[i]
			link = row['Down_link']
			if link and link != "N/A":
				filename = link.split('/')[-1].split('.')[0] + ".pdf"
				filepath = os.path.join(DOC_PATH, filename)
				if not os.path.isfile(filepath) or redownload:
					delete_doc(filepath)
					dl_doc(link, filename)
					# Set a minimum waiting time between each download
					# to avoid memory/CPU spikes and server bottlenecks
					doclist.append({'index': i + 1, 'path': filepath})
					time.sleep(0.3)
				else:
					printc("File '{}' was skipped because it was already downloaded".format(filename), 'bold')
			else:
				printc("\nDownload skipped because record has no download link:", 'yellow')
				print("Index: '{0}'\nTitle: '{1}'".format(row['index'], row['Title']))

		post_check = check_downloads(doclist)
		driver.quit()
	if post_check:
		printc("\nAll documents were successfully downloaded.", "green")
	else:
		printc("\nUh Oh... Some documents failed to download.", "red")
		cur = conn.execute("SELECT * FROM 'docs' WHERE Filepath = ''").fetchall()
		printc("\nDocument Details:", "cyan")
		print(cur)
		printc("\nDocument Amount:", "cyan")
		print(str(len(cur)))
	conn.close()

init(redownload=False)

# q = "SELECT * FROM 'docs' WHERE Filepath != ''"
# conn = connect_db(dict_factory)
# cur = conn.execute(q).fetchall()
# print(cur)