import sqlite3 as db
import PyPDF2
import os
import pandas as pd
import re


path = "C:/Users/bdeaz/OneDrive/Documentos/Beli trabajo/IMF docs/"
dirs = os.listdir(path)

docs_imf = {}
filen0 = 0

search_keyword = input("Enter word: ")

for file in dirs:
    try:
        search_count = 0
        filen0 += 1
        pdfFileObj = open("C:/Users/bdeaz/OneDrive/Documentos/Beli trabajo/IMF docs/" + file, 'rb')
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        file_name = os.path.basename(pdfFileObj.name)
        m = re.search("_cr(.+?).pdf", file_name)
        if m:
            found = m.group(1)

        for page in range(0, pdfReader.numPages):
            pageObj = pdfReader.getPage(page)
            text = pageObj.extractText().encode("utf-8")
            search_text = text.lower().split()
            for word in search_text:
                if search_keyword in word.decode("utf-8"):
                    search_count += 1

        docs_imf[filen0] = [found, search_keyword, search_count]

        print("The word {} was found in {} file {} times".format(search_keyword, found, search_count))

    except:
        pass

docs_imf_df = pd.DataFrame.from_dict(docs_imf, orient='index', columns=["File name", "%s" %(search_keyword), "Number"])
con = db.connect("C:/Users/bdeaz/PycharmProjects/createdb/IMF project/imf_ArticleIVdocs.sqlite")
docs_imf_df.to_sql("word_%s" %(search_keyword), con=con, if_exists="replace")

con.commit()
