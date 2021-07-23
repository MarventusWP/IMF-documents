import sqlite3 as db
from selenium import webdriver
import re


con = db.connect("C:/Users/bdeaz/PycharmProjects/createdb/IMF project/imf_ArticleIVdocs.sqlite")

driver = webdriver.Chrome(executable_path="C:\chromedriver.exe")


for row in con.execute("SELECT Down_link FROM 'docs'"):
    link = str(row)
    m = re.search("'(.+?)'", link)
    if m:
        found = m.group(1)
    if found != "N/A":
        driver.get(found)


driver.close()