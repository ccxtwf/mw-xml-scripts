import sqlite3
from config import logger

from typing import Iterable, Dict, Any, Optional

def convert_to_number(n: str | None) -> Optional[int]:
  if n is None:
    return None
  return int(n)

def get_wiki_metainfo_xml_head(api_entrypoint: str, exportschema: str | None = None) -> str:
  """
    Makes a request to the live wiki's API entrypoint to get the &lt;siteinfo> XML element
    relevant to the wiki's Special:Export output format

    Parameters:
      api_entrypoint (str):
        e.g. https://en.wikipedia.org/w/api.php 

    Returns: 
      (str):
        String reprensentation of the XML Element Node
  """
  
  import requests
  params = {
    "action": "query", 
    "export": "true",
    "exportnowrap": "true",
    "exportschema": exportschema,
  }
  headers = {
    "User-agent": "mw-xml-scripts"
  }
  with requests.get(api_entrypoint, params, headers=headers) as res:
    if not res.ok:
      raise Exception(f"Failed to get a response from {api_entrypoint}, HTTP Status Code: {res.status_code}, Body: {res.text}")
    return res.text
  
def create_sqlite_database(path: str, schema: Iterable[Dict[str, str]]):
  """
    Create an SQLITE3 database with the given schema.

    Parameters:
      path (str):
        Output path of the SQLITE database
      schema (Iterable[Dict[str, str]]):
        A list of table schemas to insert into the table, as defined in table_schemas.py
  """
  try:
    logger.info(f"Creating SQLite3 Database at {path}")
    db_conn = sqlite3.connect(path)
    db_cursor = db_conn.cursor()

    for table_schema in schema:
      table_name = table_schema["__tname"]
      sql = f"DROP TABLE IF EXISTS {table_name};"
      logger.info(f"Executing SQL command: {sql}")
      db_cursor.execute(sql)
      
      cols = [f"{col_name} {col_data_type}" for col_name, col_data_type in table_schema.items() if not col_name.startswith("__")]
      sql = f"CREATE TABLE {table_name}({", ".join(cols)});"
      logger.info(f"Executing SQL command: {sql}")
      db_cursor.execute(sql)
    
    db_conn.commit()
    return db_conn
  except sqlite3.DatabaseError as err:
    logger.error(f"Encountered database error: {err}")
    raise

def insert_many(db_conn: sqlite3.Connection, table_schema: Dict[str, str], data: Iterable[Any]) -> None:
  """
    Utility function to insert many rows of data at once, based on a given table schema and a dataclass

    Parameters:
      db_conn (sqlite3.Connection):
      table_schema (Dict[str, str]):
        As defined in table_schemas.py
      data (Iterable[Any]):
        List of data to be inserted
  """
  try:
    table_name = table_schema["__tname"]
    columns = [k for k in table_schema.keys() if not k.startswith("__")]
    prepared_data = []
    for _raw_datum in data:
      values = [_raw_datum.__dict__.get(col, None) for col in columns]
      prepared_data.append(tuple(values))

    sql = f"INSERT INTO {table_name}({", ".join(columns)}) VALUES({", ".join(["?" for _ in range(len(columns))])})"
    db_conn.cursor().executemany(sql, prepared_data)
    logger.info(f"Saved {len(prepared_data)} records into \"{table_name}\"")
    db_conn.commit()
  except KeyError:
    err_msg = f"\"{table_name}\" is not found in the provided schema"
    logger.error(err_msg)
    raise Exception(err_msg)
  except sqlite3.DatabaseError as err:
    logger.error(f"Encountered database error: {err}")
    raise
  except Exception as err:
    logger.error(err)
    raise