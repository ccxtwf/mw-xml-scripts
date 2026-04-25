import sqlite3
from lxml import etree
from config import (
  logger,
)
from utils import insert_many
from table_schemas import (
  NAMESPACES_TABLE_SCHEMA,
  NamespaceVm,
)
from typing import Optional, List, Tuple

def get_namespaces(db_conn: sqlite3.Connection, dump_path: str):
  tree = etree.iterparse(dump_path, tag="{*}siteinfo")
  namespaces = get_site_namespace_info(next(tree, None))
  if namespaces is not None:
    insert_many(
      db_conn=db_conn,
      table_schema=NAMESPACES_TABLE_SCHEMA,
      data=namespaces
    )
    logger.info(f"Saved namespace information")

def get_site_namespace_info(arg: Tuple[str, etree.Element] | None) -> Optional[List[NamespaceVm]]:
  if arg is None:
    return None
  _, xmlTree = arg
  res = []
  namespaces = xmlTree.find("{*}namespaces").findall("{*}namespace")
  for namespace in namespaces:
    ns_id = namespace.get('key', None)
    ns_title = namespace.text or "(Main)"
    res.append(NamespaceVm(ns_id, ns_title))
  return res