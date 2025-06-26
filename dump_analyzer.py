"""
Use this script to get the summary of wikipage/revision information within a MediaWiki XML dump.
The summary is outputted onto an SQLITE3 database file.

Output Schema:
=============================================================
| Namespaces                                                |
=============================================================
| id              || INTEGER NOT NULL                       |
| ns              || TEXT NULLABLE                          |
=============================================================
=============================================================
| WikipageOverviews                                         |
=============================================================
| id              || INTEGER NOT NULL                       |
| ns              || INTEGER NULLABLE                       |
| title           || TEXT NULLABLE                          |
| num_revisions   || INTEGER NULLABLE                       |
| last_edited     || TEXT NULLABLE                          |
| redirect_target || TEXT NULLABLE                          |
=============================================================

Example SQL Summarization Statement:
  SELECT 
    w.ns, 
    CASE WHEN w.redirect_target IS NULL THEN 'Non-redirects' ELSE 'Redirects' END AS "page_type", 
    COUNT(w.id) AS "num_pages", 
    SUM(w.num_revisions) AS "num_revisions", 
    MAX(w.last_edited) AS "last_edited" 
  FROM Wikipages w 
  GROUP BY ns, w.redirect_target IS NULL;
   

Config:
 - DUMP: The filepath of the MediaWiki XML dump
 - OUTPUT_SQL_FILE: The filepath of the output SQLITE3 database
 - OUTPUT_LOG_ERRORS: The filepath of the script's error log
 - CONST_UNPACK_ITERATIONS: Adjust based on your computer's RAM
"""

import sqlite3

DUMP = "C:\\Users\\path\\to\\file.xml"
OUTPUT_SQL_FILE = "vlw_fandom_all_pages_summary_26_june.db"
OUTPUT_LOG_ERRORS = "log_analyze_dump_error.txt"

CONST_UNPACK_ITERATIONS = 100

# ==============================================
# === DON'T CHANGE ANYTHING BEYOND THIS LINE ===
# ==============================================

import xml.etree.ElementTree as ET

from typing import Tuple, Optional, List

XML_DEFINITION = "{http://www.mediawiki.org/xml/export-0.11/}"

def create_database() -> sqlite3.Connection:
  print(f"Creating SQLite3 Database at {OUTPUT_SQL_FILE}")
  db_conn = sqlite3.connect(OUTPUT_SQL_FILE)
  db_cursor = db_conn.cursor()
  
  db_cursor.execute("DROP TABLE IF EXISTS Namespaces")
  db_cursor.execute("CREATE TABLE Namespaces(id INTEGER NOT NULL, ns TEXT)")
  db_cursor.execute("DROP TABLE IF EXISTS WikipageOverviews")
  db_cursor.execute("CREATE TABLE WikipageOverviews(id INTEGER NOT NULL, ns INTEGER, title TEXT, num_revisions INTEGER, last_edited TEXT, redirect_target TEXT)")
  return db_conn

def summarize_dump(db_conn: sqlite3.Connection):
  tree = ET.parse(DUMP)
  root = tree.getroot()
  xml_iter = iter(root)

  num_pages = 0
  num_revisions = 0
  
  namespaces = get_site_namespace_info(next(xml_iter, None))
  db_conn.cursor().executemany(
    f"INSERT INTO Namespaces(id, ns) VALUES(?, ?)",
    namespaces
  )
  db_conn.commit()
  print(f"Saved namespace information")

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
    res = [get_page_summary(i) for i in fetched]
    res = [f for f in res if f is not None]
    # print(res)
    n = len(res)
    if n > 0:
      num_pages += n
      num_revisions += sum(map(lambda t: t[3], res))
      db_conn.cursor().executemany(
        f"INSERT INTO WikipageOverviews(id, ns, title, num_revisions, last_edited, redirect_target) VALUES(?, ?, ?, ?, ?, ?)",
        res
      )
      db_conn.commit()
      print(f"Saved {n} records")
  print(f"{num_pages} pages")
  print(f"{num_revisions} revisions")

def get_site_namespace_info(xmlTree: Optional[ET.Element]) -> Optional[List[Tuple[int, str]]]:
  if xmlTree is None:
    return None
  if xmlTree.tag == f"{XML_DEFINITION}siteinfo":
    res = []
    namespaces = xmlTree.find(f"{XML_DEFINITION}namespaces").findall(f"{XML_DEFINITION}namespace")
    for namespace in namespaces:
      ns_id = namespace.get('key', None)
      ns_title = namespace.text or "(Main)"
      res.append((ns_id, ns_title))
    return res

def get_page_summary(xmlTree: Optional[ET.Element]) -> Optional[Tuple[int, int, str, int, str, Optional[str]]]:
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
    redirect = None if redirect is None else redirect.get('title', '')
    revs = xmlTree.findall(f"{XML_DEFINITION}revision")
    n_rev = len(revs)
    if n_rev == 0:
      print(f"XML Element has no revisions")
      return (id, ns, title, n_rev, None, redirect)
    last_edited = "1960-01-01T00:00:00Z"
    for i in range(n_rev):
      cur_timestamp = revs[i].find(f"{XML_DEFINITION}timestamp")
      if cur_timestamp is not None and cur_timestamp.text >= last_edited:
        last_edited = cur_timestamp.text

    return (id, ns, title, n_rev, last_edited, redirect)
  else:
    print(f"Encountered Xml Element {xmlTree.tag}")
    with open(OUTPUT_LOG_ERRORS, "a") as f:
      f.write(f"Encountered Xml Element {xmlTree.tag}\n")
    return None

if __name__ == "__main__":
  db_conn = create_database()
  summarize_dump(db_conn)