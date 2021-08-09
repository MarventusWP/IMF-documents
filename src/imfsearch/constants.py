import os

ROOT_PATH = os.getcwd()

DB_PATH = os.path.join(ROOT_PATH, '_data')
DB_NAME = 'imf_article_iv.sqlite'
DB_FULLPATH = os.path.join(DB_PATH, DB_NAME)

DOC_PATH = os.path.join(ROOT_PATH, '_docs')

IMF_URL = "https://www.imf.org/"