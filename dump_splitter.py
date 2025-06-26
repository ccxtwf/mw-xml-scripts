"""
Use this script to split a MediaWiki XML dump into a database, indexable by each page's 
namespace, page ID and page title.
The summary is outputted onto an SQLITE3 database file.

Output Schema:
=============================================================
| Wikipages                                                 |
=============================================================
| id              || INTEGER NOT NULL                       |
| ns              || INTEGER NULLABLE                       |
| title           || TEXT NULLABLE                          |
| contents        || INTEGER NULLABLE                       |
| redirect_to     || TEXT NULLABLE                          |
=============================================================

Config:
 - DUMP: The filepath of the MediaWiki XML dump
 - OUTPUT_SQL_FILE: The filepath of the output SQLITE3 database
 - OUTPUT_LOG_ERRORS: The filepath of the script's error log
 - CONST_UNPACK_ITERATIONS: Adjust based on your computer's RAM
"""

import sqlite3

DUMP = "C:\\Users\\path\\to\\file.xml"
OUTPUT_SQL_FILE = "vlw_fandom_all_pages_26_june.db"
OUTPUT_LOG_ERRORS = "log_analyze_dump_error.txt"

CONST_UNPACK_ITERATIONS = 100

# ==============================================
# === DON'T CHANGE ANYTHING BEYOND THIS LINE ===
# ==============================================

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring

from typing import Tuple, Optional

XML_DEFINITION = "{http://www.mediawiki.org/xml/export-0.11/}"

def create_database() -> sqlite3.Connection:
  print(f"Creating SQLite3 Database at {OUTPUT_SQL_FILE}")
  db_conn = sqlite3.connect(OUTPUT_SQL_FILE)
  db_cursor = db_conn.cursor()
  
  db_cursor.execute("DROP TABLE IF EXISTS Wikipages")
  db_cursor.execute("CREATE TABLE Wikipages(id INTEGER NOT NULL, ns INTEGER, title TEXT, contents TEXT, redirect_to TEXT)")
  return db_conn

def split_dump(db_conn: sqlite3.Connection):
  tree = ET.parse(DUMP)
  root = tree.getroot()
  xml_iter = iter(root)
  while True:
    fetched = []
    cur = None
    for _ in range(CONST_UNPACK_ITERATIONS):
      cur = next(xml_iter, None)
      if cur is None:
        print("FINISHED ITERATING")
        break
      fetched.append(cur)
    if len(fetched) == 0:
      break
    res = [get_page_contents(i) for i in fetched]
    res = [f for f in res if f is not None]
    # print(res)
    n = len(res)
    if n > 0:
      db_conn.cursor().executemany(
        f"INSERT INTO Wikipages(id, ns, title, contents, redirect_to) VALUES(?, ?, ?, ?, ?)",
        res
      )
      db_conn.commit()
      print(f"Saved {n} records")

def get_page_contents(xmlTree: Optional[ET.Element]) -> Optional[Tuple[int, int, str, int, str, Optional[str]]]:
  if xmlTree is None:
    return None
  if xmlTree.tag == f"{XML_DEFINITION}page":
    id = xmlTree.find(f"{XML_DEFINITION}id")
    id = None if id is None else int(id.text)
    ns = xmlTree.find(f"{XML_DEFINITION}ns")
    ns = None if ns is None else int(ns.text)
    title = xmlTree.find(f"{XML_DEFINITION}title")
    title = None if title is None else title.text
    redirect = xmlTree.find(f"{XML_DEFINITION}redirect")
    redirect = None if redirect is None else redirect.get('title', None)
    contents = tostring(xmlTree, encoding='unicode')
    return (id, ns, title, contents, redirect)
  else:
    print(f"Encountered Xml Element {xmlTree.tag}")
    with open(OUTPUT_LOG_ERRORS, "a") as f:
      f.write(f"Encountered Xml Element {xmlTree.tag}\n")
    return None

if __name__ == "__main__":
  db_conn = create_database()
  split_dump(db_conn)