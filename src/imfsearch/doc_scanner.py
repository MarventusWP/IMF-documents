import sqlite3 as db
import PyPDF2
import os
import pandas as pd
import re

from imfsearch.constants import DOC_PATH, DB_FULLPATH

def init():
    dirs = os.listdir(DOC_PATH)

    docs_imf = {}
    filen0 = 0

    search_keyword = input("Type a keyword to search for in the documents: ")

    for file in dirs:
        try:
            search_count = 0
            filen0 += 1
            pdfFileObj = open(DOC_PATH + file, 'rb')
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            file_name = os.path.basename(pdfFileObj.name)
            m = re.search("_cr(.+?).pdf", file_name)
            print("m", m)
            if m:
                found = m.group(1)
                print("found:", found)

            # for page in range(0, pdfReader.numPages):
            #     pageObj = pdfReader.getPage(page)
            #     text = pageObj.extractText().encode("utf-8")
            #     search_text = text.lower().split()
            #     for word in search_text:
            #         if search_keyword in word.decode("utf-8"):
            #             search_count += 1

            # docs_imf[filen0] = [found, search_keyword, search_count]

            # print("The word {} was found in {} file {} times".format(search_keyword, found, search_count))

        except:
            pass

    docs_imf_df = pd.DataFrame.from_dict(docs_imf, orient='index', columns=["Filename", "%s" %(search_keyword), "Number"])
    con = db.connect(DB_FULLPATH)
    docs_imf_df.to_sql("word_%s" %(search_keyword), con=con, if_exists="replace")

    con.commit()

# con= db.connect(DB_FULLPATH)
# cur = con.cursor()
# cur.execute("DROP TABLE 'word_humanitarian'")
# con.commit()
# cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
# print(cur.fetchall())
init()
