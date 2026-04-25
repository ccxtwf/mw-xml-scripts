import sqlite3
from lxml import etree
from itertools import batched
from html import unescape
from config import (
  logger,
  MAX_PAGE_NODES_TO_UNPACK
)
from get_namespaces import get_namespaces
from utils import (
  convert_to_number, 
  insert_many,
  create_sqlite_database,
)
from table_schemas import (
  NAMESPACES_TABLE_SCHEMA,
  WIKIPAGE_OVERVIEWS_TABLE_SCHEMA,
  WIKIPAGE_REVISIONS_TABLE_SCHEMA,
  WIKIPAGE_CONTENT_XMLS_TABLE_SCHEMA,
  WikipageOverviewVm,
  WikipageRevisionVm,
  WikipageContentXmlVm,
)
from typing import Iterable, Callable, Tuple, Dict, List, Literal, Optional, Any

def get_wikipages(
    dump_path: str, 
    output_path: str,
    options: List[Literal["overview", "page_xml", "revisions"]],
  ):

  ops: Iterable[Tuple[Callable[[etree.Element | None], Optional[Any]], Dict[str, str], bool]] = []
  schema: List[Dict[str, str]] = [NAMESPACES_TABLE_SCHEMA]
  if "overview" in options:
    ops.append((get_page_summary, WIKIPAGE_OVERVIEWS_TABLE_SCHEMA, False))
    schema.append(WIKIPAGE_OVERVIEWS_TABLE_SCHEMA)
  if "page_xml" in options:
    ops.append((get_page_contents, WIKIPAGE_CONTENT_XMLS_TABLE_SCHEMA, False))
    schema.append(WIKIPAGE_CONTENT_XMLS_TABLE_SCHEMA)
  if "revisions" in options:
    ops.append((get_page_revisions, WIKIPAGE_REVISIONS_TABLE_SCHEMA, True))
    schema.append(WIKIPAGE_REVISIONS_TABLE_SCHEMA)
  
  db_conn = create_sqlite_database(path=output_path, schema=schema)

  get_namespaces(db_conn=db_conn, dump_path=dump_path)

  tree = etree.iterparse(dump_path, tag="{*}page")

  num_pages = 0
  for batch in batched(tree, MAX_PAGE_NODES_TO_UNPACK):
    num_pages += len(batch)
    # run each operation 
    [treat_batch(batch, db_conn, treat_page, schema, flatten_results) for treat_page, schema, flatten_results in ops]

  logger.info(f"Iterated through {num_pages} pages")

def treat_batch(fetched: Tuple[str, etree.Element], db_conn: sqlite3.Connection, treat_page: Callable[[etree.Element], None], table_schema: Dict[str, str], flatten_results: bool = False):
  res = [_f for _f in (treat_page(_page) for _, _page in fetched) if _f is not None]
  if len(res) > 0:
    if flatten_results:
      res = [x for xs in res for x in xs] # type: ignore
    insert_many(
      db_conn=db_conn,
      table_schema=table_schema,
      data=res
    )

def get_page_summary(xmlTree: etree.Element | None) -> Optional[WikipageOverviewVm]:
  if xmlTree is None:
    return None
  id = convert_to_number(xmlTree.findtext("{*}id", None))
  ns = convert_to_number(xmlTree.findtext("{*}ns", None))
  title = xmlTree.findtext("{*}title", None)
  redirect = xmlTree.find("{*}redirect", None)
  redirect = None if redirect is None else redirect.get('title', '')
  revs = xmlTree.findall("{*}revision")
  n_rev = len(revs)
  if n_rev == 0:
    logger.info(f"XML Element [id={id}, ns={ns}, title={title}] has no revisions")
    return WikipageOverviewVm(
      id=id or 0, 
      ns=ns, 
      title=title, 
      num_revisions=n_rev, 
      last_edited=None, 
      redirect_target=redirect,
      size=None
    )
  size = None
  last_edited = "1960-01-01T00:00:00Z"
  for i in range(n_rev):
    cur_timestamp = revs[i].findtext("{*}timestamp", None)
    if cur_timestamp is not None and cur_timestamp >= last_edited:
      last_edited = cur_timestamp
      text_node = revs[i].find("{*}text", None)
      if text_node is not None:
        size = text_node.get("bytes")
  return WikipageOverviewVm(
    id=id or 0, 
    ns=ns, 
    title=title, 
    num_revisions=n_rev, 
    last_edited=last_edited, 
    redirect_target=redirect,
    size=size
  )

def get_page_contents(xmlTree: etree.Element | None) -> Optional[WikipageContentXmlVm]:
  if xmlTree is None:
    return None
  id = convert_to_number(xmlTree.findtext("{*}id", None))
  ns = convert_to_number(xmlTree.findtext("{*}ns", None))
  title = xmlTree.findtext("{*}title", None)
  redirect = xmlTree.find("{*}redirect", None)
  redirect = None if redirect is None else redirect.get('title', '')
  contents = etree.tostring(xmlTree, encoding='unicode')
  return WikipageContentXmlVm(
    id=id or 0,
    ns=ns,
    title=title,
    contents=contents,
    redirect_to=redirect
  )

def get_page_revisions(xmlTree: etree.Element | None) -> Optional[Iterable[WikipageRevisionVm]]:
  if xmlTree is None:
    return None
  id = convert_to_number(xmlTree.findtext("{*}id", None))
  revs = xmlTree.findall("{*}revision")
  if len(revs) == 0:
    logger.info(f"XML Element [id={id}, ns={xmlTree.fintext("{*}ns", None)}, title={xmlTree.fintext("{*}title", None)}] has no revisions")
    return None
  res = []
  for rev in revs:
    revid = convert_to_number(rev.findtext("{*}id", None))
    parentid = convert_to_number(rev.findtext("{*}parentid", None))
    timestamp = rev.findtext("{*}timestamp", None)
    contributor = rev.findtext("{*}contributor/{*}username", rev.findtext("{*}contributor/{*}ip", None))
    origin = convert_to_number(rev.findtext("{*}origin", None))
    model = rev.findtext("{*}model", None)
    rformat = rev.findtext("{*}format", None)
    size = None
    sha1 = None
    text = None
    text_node = rev.find("{*}text", None)
    if text_node is not None:
      if text_node.text is not None:
        text = unescape(text_node.text)
      size = text_node.get("bytes")
      sha1 = text_node.get("sha1")
    res.append(WikipageRevisionVm(
      pageid=id or 0,
      revid=revid or 0,
      parentid=parentid,
      timestamp=timestamp,
      contributor=contributor,
      origin=origin,
      model=model,
      format=rformat,
      size=size,
      sha1=sha1,
      text=text
    ))
  return res