import sqlite3 as db
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re


driver = webdriver.Chrome(executable_path="C:\chromedriver.exe")

driver.get("https://www.imf.org/en/publications/search")

driver.minimize_window()

drop_type = Select(driver.find_element_by_xpath('//*[@id="SeriesMultiSelect"]'))
drop_type.select_by_value("IMF Staff Country Reports")

driver.find_element_by_xpath('//*[@id="TitleInput"]').send_keys("Article IV")

drop_time = Select(driver.find_element_by_xpath('//*[@id="DateWhenSelect"]'))
drop_time.select_by_visible_text("During")

drop_year = Select(driver.find_element_by_xpath('//*[@id="YearSelect"]'))
year = str(input("Enter a year: "))
drop_year.select_by_value(year)

driver.find_element_by_xpath('//*[@id="SearchButton"]').click()
url = driver.current_url

npo_docs = {}
docn0 = 0

while True:
    data = requests.get(url).text
    soup = BeautifulSoup(data, 'html.parser')

    docs = soup.find_all("div", {"class":"result-row pub-row"})
    for doc in docs:
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
        found4 = found2 + found3

        date = doc.findAll("p")[2].text.strip()
        link = "https://www.imf.org" + doc.find("a").get("href")

        doc_data = requests.get(link).text
        doc_soup = BeautifulSoup(doc_data, "html.parser")
        doc_soup_docs = doc_soup.findAll("section")[0]
        if len(doc_soup_docs.findAll("p", {"class":"pub-desc"})) == 3:
            doc_summary = doc_soup_docs.findAll("p", {"class":"pub-desc"})[2].text
            down_link = "N/A"
        else:
            try:
                down_link = "https://www.imf.org" + doc_soup_docs.find("a", {"class": "piwik_download"}).get("href")
                doc_summary = doc_soup_docs.findAll("p", {"class": "pub-desc"})[3].text
            except:
                doc_summary = doc_soup_docs.findAll("p", {"class": "pub-desc"})[3].text
                down_link = "N/A"


        docn0 += 1

        npo_docs[docn0] = [title, series, date, link, doc_summary, down_link, found4, int(year)]

    if soup.find("a", {"class":"next"}):
        url_tag = soup.find("a", {"class":"next"})
        url = url_tag.get("href")
    else:
        break

print("Total docs:", docn0)

npo_docs_df = pd.DataFrame.from_dict(npo_docs, orient='index', columns=["Title", "Series", "Date", "Link", "Summary", "Down_link", "Number", "Year"])

con = db.connect("C:/Users/bdeaz/PycharmProjects/createdb/IMF project/imf_ArticleIVdocs.sqlite")
npo_docs_df.to_sql("docs", con=con, if_exists="append")

con.commit()

driver.close()