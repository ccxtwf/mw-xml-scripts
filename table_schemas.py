from dataclasses import dataclass

@dataclass
class NamespaceVm:
  id: int
  ns: str | None

@dataclass
class WikipageOverviewVm:
  id: int
  ns: int | None
  title: str | None
  num_revisions: int | None
  last_edited: str | None
  redirect_target: str | None
  size: int | None

@dataclass
class WikipageRevisionVm:
  pageid: int
  revid: int
  parentid: int | None
  timestamp: str | None
  contributor: str | None
  origin: int | None
  model: str | None
  format: str | None
  size: int | None
  sha1: str | None
  text: str | None

@dataclass
class WikipageContentXmlVm:
  id: int
  ns: int | None
  title: str | None
  contents: str | None
  redirect_to: str | None

NAMESPACES_TABLE_SCHEMA = {
  "__tname": "Namespaces",
  "__dataclass": NamespaceVm,
  "id": "INTEGER NOT NULL",
  "ns": "TEXT",
}
WIKIPAGE_OVERVIEWS_TABLE_SCHEMA = {
  "__tname": "WikipageOverviews",
  "__dataclass": WikipageOverviewVm,
  "id": "INTEGER NOT NULL",
  "ns": "INTEGER",
  "title": "TEXT",
  "num_revisions": "INTEGER",
  "last_edited": "TEXT",
  "redirect_target": "TEXT",
  "size": "INTEGER",
}
WIKIPAGE_REVISIONS_TABLE_SCHEMA = {
  "__tname": "WikipageRevisions",
  "__dataclass": WikipageRevisionVm,
  "pageid": "INTEGER NOT NULL",
  "revid": "INTEGER NOT NULL",
  "parentid": "INTEGER",
  "timestamp": "TEXT",
  "contributor": "TEXT",
  "origin": "INTEGER",
  "model": "TEXT",
  "format": "TEXT",
  "size": "INTEGER",
  "sha1": "TEXT",
  "text": "TEXT",
}
WIKIPAGE_CONTENT_XMLS_TABLE_SCHEMA = {
  "__tname": "WikipageContentXmls",
  "__dataclass": WikipageContentXmlVm,
  "id": "INTEGER NOT NULL",
  "ns": "INTEGER",
  "title": "TEXT",
  "contents": "TEXT",
  "redirect_to": "TEXT"
}