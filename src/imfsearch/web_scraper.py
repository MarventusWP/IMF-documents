import sqlite3 as db
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import math, os, re, requests, time
from termcolor import colored, cprint

from imfsearch.drivers import chrome_driver
from imfsearch.constants import DB_PATH, DB_FULLPATH, IMF_URL
from imfsearch.helpers import is_field_in_db

### GLOBALS ###
# chrome driver
driver = None
# dry run mode
# (Pass True in order to disable scraping and DB modifications)
dry_run = False

def launch_driver(url = None, start_minimized = True):
	global driver
	if driver == None:
		driver = chrome_driver.install()
	if url: driver.get(url)
	if start_minimized:
		time.sleep(1)
		driver.minimize_window()

def kill_driver():
	print("Quitting Chrome Driver...\n")
	driver.quit()

def do_search_loop(criteria):
	if(
		criteria['start_year'] == '' or
		(criteria['title'] == '' and criteria['keywords'] == '' and criteria['series'] == '')
	):
		cprint("\nYour search criteria are too wide. Please try again with more specific criteria.", "red", attrs=["bold"])
		return False
	start_year = criteria['start_year']
	end_year = criteria['end_year']
	print("\nSubmitting search terms to Chrome driver. Please wait...")
	# Update Title field
	driver.find_element_by_id('TitleInput').send_keys(criteria['title'])
	# Update Author field
	driver.find_element_by_id('AuthorEditorInput').send_keys(criteria['author'])
	# Update Subject/Keyword field
	driver.find_element_by_id('SubjectKeywordInput').send_keys(criteria['keywords'])
	# Update Series field
	Select(driver.find_element_by_id('SeriesMultiSelect')).select_by_value(criteria['series'])
	# Update Date/When field
	Select(driver.find_element_by_id('DateWhenSelect')).select_by_value("During")

	current_year = 0
	number_docs = 0
	npo_docs = {}
	repeated_action = ''

	for current_year in range(start_year, end_year + 1):

		# Search for current_year and wait until results are loaded
		Select(driver.find_element_by_id('YearSelect')).select_by_value(str(current_year))
		driver.find_element_by_id('SearchButton').click()
		search_complete = False
		while not search_complete:
			search_complete = driver.execute_script('return document.readyState;') == 'complete'
			time.sleep(0.1)

		url = driver.current_url
		total_pages = 0
		records_per_page = 0
		current_page = 1
		total_records_elem = None
		yearly_docs = 0

		data = requests.get(url).text
		soup = BeautifulSoup(data, 'html.parser')

		total_records_elem = driver.find_element_by_css_selector('.search-results .resultsdoc span')
		yearly_docs = int(total_records_elem.text.strip())
		if yearly_docs == 0:
			continue

		# Check if records exist for the current year, and if so, prompt them for an action.
		if is_field_in_db('docs', 'Year', 'Year', current_year):
			if not repeated_action:
				prompt_repeated = prompt_year_repeated(current_year)
				if prompt_repeated.find('ALL') != -1:
					repeated_action = prompt_repeated
			if repeated_action.find('SKIP') != -1 or prompt_repeated.find('SKIP') != -1:
				# Update number of documents to keep track of total processed items.
				number_docs += yearly_docs
				continue

		cprint(f"\nFound {yearly_docs} documents for the year {current_year}. Processing data.\nThis may take a while...", "yellow")

		docs = soup.find_all("div", {"class":"result-row pub-row"})
		records_per_page = len(docs)
		total_pages = math.ceil(float(yearly_docs / records_per_page))

		while not dry_run and current_page <= total_pages:

			print("\nProcessing page {0} of {1}...\n".format(current_page, total_pages))

			if current_page > 1:
				data = requests.get(url).text
				soup = BeautifulSoup(data, 'html.parser')
				docs = soup.find_all("div", {"class":"result-row pub-row"})

			for i in range(len(docs)):
				doc = docs[i]
				title = doc.find("a").text.strip()
				series = doc.findAll("p")[1].text.strip()

				m = re.search("No. (.+)", series)
				if m:
					found = m.group(1)
				n = re.search("(.+)/", found)
				if n:
					found2 = n.group(1)
				o = re.search("/(.+)", found)
				if o:
					found3 = o.group(1)
				doc_number = found2 + found3

				date = doc.findAll("p")[2].text.strip()
				link = IMF_URL + doc.find("a").get("href")

				doc_data = requests.get(link).text
				doc_soup = BeautifulSoup(doc_data, "html.parser")
				doc_soup_docs = doc_soup.findAll("section")[0]
				if len(doc_soup_docs.findAll("p", {"class":"pub-desc"})) == 3:
					doc_summary = doc_soup_docs.findAll("p", {"class":"pub-desc"})[2].text
					down_link = "N/A"
				else:
					try:
						down_link = IMF_URL + doc_soup_docs.find("a", {"class": "piwik_download"}).get("href")
						doc_summary = doc_soup_docs.findAll("p", {"class": "pub-desc"})[3].text
					except:
						doc_summary = doc_soup_docs.findAll("p", {"class": "pub-desc"})[3].text
						down_link = "N/A"

				number_docs += 1

				npo_docs[number_docs] = [title, series, date, link, doc_summary, down_link, doc_number, int(current_year), ""]

			next_button = soup.find("a", {"class":"next"})
			if next_button:
				url = next_button.get("href")
				current_page += 1
				driver.get(url)
			else:
				break

	cprint(f"\nFinished processing all {number_docs} documents.\n", 'green', attrs=['bold'])
	return npo_docs

def input_yes_no(question):
	return input(f"\n{question}\n[{colored('Y', 'yellow', attrs=['bold'])}]yes | [{colored('N','yellow', attrs=['bold'])}]no ").lower()


def store_in_db(docs):
	print("Persisting document metadata in database. Please wait...\n")

	try:
		npo_docs_df = pd.DataFrame.from_dict(docs, orient='Index', columns=["Title", "Series", "Date", "Link", "Summary", "Down_link", "Number", "Year", "Filepath"])
		os.makedirs(DB_PATH, exist_ok=True)
		conn = db.connect(DB_FULLPATH)
		npo_docs_df.to_sql("docs", con=conn, if_exists="append")
		conn.commit()
		conn.close()
		cprint("\nDocument metadata successfully stored in the database.\n", "green")

	except:
		cprint("There was an unexpected exception while writing to the database.", "red")

def check_db(total_found):
	cprint("\nChecking number of records in DB against total records found...", "yellow")
	conn = db.connect(DB_FULLPATH)
	cur = conn.cursor()
	with conn:
		cur.execute("SELECT * FROM 'docs'")
		data = cur.fetchall()
		amount = len(data)
		print(f"\nTotal records found: {colored(total_found, 'cyan')}")
		print(f"Total records in DB: {colored(amount, 'cyan')}")
		if total_found == amount:
			cprint('\nSweet! Totals match. All is good!\n', 'green', attrs=['bold'])
		else:
			cprint("\nUh oh... Totals don't match. Please query the DB for more info.\n", 'red', attrs=['bold'])

def prompt_user_search():
	mandatory = colored("*", "red", attrs=["bold"])
	at_least_one = colored("*", "blue", attrs=["bold"])
	print(f"{colored('LEGEND:', 'white', attrs=['bold'])}\n{mandatory}  Mandatory\n{at_least_one}  At least one\n")

	start_year = input(f"\nPlease enter the {colored('START YEAR', 'yellow')} for your search {mandatory}: ")
	start_year = int(start_year or '0')

	end_year = int(input(f"\nPlease enter the {colored('END YEAR', 'yellow')} for your search: "))
	if not end_year:
		cprint(f'No end year specified. The search will be conducted only in selected start year ("{start_year}").', 'yellow')
		end_year = start_year

	title = input(f"\nPlease enter a partial or full {colored('TITLE', 'yellow')} {at_least_one}: ")

	author = input(f"\nPlease enter the name of the {colored('EDITOR', 'yellow')} or {colored('AUTHOR', 'yellow')} {at_least_one}: ")

	keywords = input(f"\nYou can narrow down your search by {colored('SUBJECT', 'yellow')} or {colored('KEYWORDS','yellow')} {at_least_one}: ")

	series_dropdown = Select(driver.find_element_by_id("SeriesMultiSelect"))
	series_options = series_dropdown.options
	series = ''
	print(f"\n[{colored('1', 'yellow')}] - All Series")
	for i in range(2, len(series_options)):
		print(f"[{colored(i, 'yellow')}] - {series_options[i].get_attribute('value')}")
	series_selected = input(f"\nPlease enter the corresponding number of the document {colored('SERIES', 'yellow')} you wish to search for {at_least_one}: ")
	if series_selected:
		series = series if series_selected == "1" else series_options[int(series_selected)].get_attribute('value')

	data = {}
	for var in ['start_year', 'end_year', 'title', 'author', 'keywords', 'series']:
		data[var] = eval(var)
	cprint("\nSelected search criteria:", "white", attrs=["bold"])
	for key in data:
		print(colored(f"{key.replace('_', ' ').upper()}", "yellow") + f': "{data[key]}"')
	confirm_prompt = input_yes_no("Confirm your selection?")
	confirmed = confirm_prompt == "y" or confirm_prompt == "yes"
	if not confirmed:
		start_over = input_yes_no("Your search criteria have been discarded. Would you like to start over?")
		if start_over == "n" or start_over == "no":
			return
	return data if confirmed else False

def prompt_year_repeated(year):
	cprint(f"\nIt appears the database already contains records for documents from {year}. How would you like to proceed?", 'yellow')
	options = [
		f"{colored('SKIP CURRENT', 'cyan')} year {year} and prompt me again for future years.",
		f"{colored('PROCESS CURRENT','cyan')} year {year} and prompt me again for future years.",
		f"{colored('SKIP ALL', 'cyan')} years already in the database",
		f"{colored('PROCESS ALL', 'cyan')} years already in the database"
	]
	for num, option in enumerate(options, start=1):
		print(f"[{colored(num, 'yellow')}] {option}")
	selection = input( colored("\nPlease choose an option: ", 'white', attrs=['bold']) )
	#upper = [char for char in options[int(selection)] if char.isupper() or char.isspace()]
	upper = list(filter(lambda x: x.isupper() or x.isspace(), options[int(selection)-1]))
	return re.sub(r'\s', '_', ''.join(upper).strip())

def init(dry = dry_run):
	global dry_run
	dry_run = dry
	# os.system('cls')
	cprint("\nWelcome to the IMF document search script!", "white", attrs=["bold"])
	print("""
This tool will let you scan through IMF's document search page and selet all the criteria of your choice to perform searches.
All relevant document metadata can be stored into a custom database so that the documents of your interest can later be
downloaded locally and searched for keywords. Pretty sweet, right?\n""")
	input(colored("Press 'Enter' to get started...", "white", attrs=["reverse"]))
	#Start chrome driver
	launch_driver(IMF_URL + "en/publications/search")
	user_data = False
	# Prompt user until search criteria are confirmed
	while user_data == False:
		user_data = prompt_user_search()
	# Run search or Quit
	if not user_data: return
	search_results = do_search_loop(user_data)
	# Store results (if found)fSub
	total_docs = len(search_results)
	if total_docs > 0:
		store_in_db(search_results)
		# Run post storage check in Db
		check_db(total_docs)
	# Quit chrome driver
	# kill_driver()

init()