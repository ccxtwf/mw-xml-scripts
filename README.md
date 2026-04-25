# MediaWiki XML Scripts

This is a Python package used to analyze, partition or split into chunks a MediaWiki XML dump. Originally written with the Vocaloid Lyrics Wiki in mind (100,000+ pages, 1M+ revisions, average page size of 2,000-10,000 bytes).

## General steps

### Setup

This package requires the following:
 - Python 3.12+
 - Installation of lxml. You can install this using `pip install lxml` or by using your preferred package manager.

To start using, either clone this repository:
```sh
git clone https://github.com/ccxtwf/mw-xml-scripts.git
```

Or download the source code from [GitHub Releases](https://github.com/ccxtwf/mw-xml-scripts/releases/new).

Analyzed results will be saved onto a SQLITE database file. You can use an interactive database browser such as [SQLITE Browser](https://sqlitebrowser.org) or [DBeaver](https://dbeaver.io) to view this database file. 

### How to use

On a Python file, write the following:
```py
from get_wikipages import get_wikipages

get_wikipages(
  # Input filepath
  dump_path="/path/to/dump.xml",
  
  # Output filepath
  output_path="/path/to/sqlite/file.xml",
  
  # Select one or more of these options
  options=["overview", "page_xml", "revisions"], 
)
```

`options=[...]` controls the properties that will be parsed by this package. `overview` returns the basic page overviews, including the number of revisions and latest edited date. `page_xml` splits the individual &lt;page&gt; XML nodes (including multiple revisions for each &lt;page&gt; node), and can be useful if trying to select a number of pages to be imported/exported into your wiki. `revisions` splits the individual revisions of each page, which you can use for more advanced analysis. You can choose a multiple of these options on a single run. 

The following describes the table schemas that are created by each option:

**overview**

<table>
<caption><b>WikipageOverviews</b></caption>
<tr>
<th>Column Name</th>
<th>Description</th>
<th>Data Type</th>
</tr>
<tr>
<td><code>id</code></td>
<td>Page ID</td>
<td>INTEGER NON-NULLABLE</td>
</tr>
<tr>
<td><code>ns</code></td>
<td>Namespace numeric ID</td>
<td>INTEGER</td>
</tr>
<tr>
<td><code>title</code></td>
<td>Page title</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>num_revisions</code></td>
<td>Number of revisions</td>
<td>INTEGER</td>
</tr>
<tr>
<td><code>last_edited</code></td>
<td>Last edit timestamp</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>redirect_target</code></td>
<td>If the page is a redirect, then this field details the title of the page it redirects towards.</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>size</code></td>
<td>The page size in bytes.</td>
<td>INTEGER</td>
</tr>
</table>

**page_xml**

<table>
<caption><b>WikipageContentXmls</b></caption>
<tr>
<th>Column Name</th>
<th>Description</th>
<th>Data Type</th>
</tr>
<tr>
<td><code>id</code></td>
<td>Page ID</td>
<td>INTEGER NON-NULLABLE</td>
</tr>
<tr>
<td><code>ns</code></td>
<td>Namespace numeric ID</td>
<td>INTEGER</td>
</tr>
<tr>
<td><code>title</code></td>
<td>Page title</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>contents</code></td>
<td>The string representation of the &lt;page&gt; XML node</td>
<td>TEXT</td>
</tr>
</table>

**revisions**

<table>
<caption><b>WikipageRevisions</b></caption>
<tr>
<th>Column Name</th>
<th>Description</th>
<th>Data Type</th>
</tr>
<tr>
<td><code>pageid</code></td>
<td>Page ID</td>
<td>INTEGER NON-NULLABLE</td>
</tr>
<tr>
<td><code>revid</code></td>
<td>Revision ID</td>
<td>INTEGER NON-NULLABLE</td>
</tr>
<tr>
<td><code>parentid</code></td>
<td>-</td>
<td>INTEGER</td>
</tr>
<tr>
<td><code>timestamp</code></td>
<td>Edit timestamp</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>contributor</code></td>
<td>Username (if edit was made by a logged in user) or IP address (if made by anonymous)</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>origin</code></td>
<td>-</td>
<td>INTEGER</td>
</tr>
<tr>
<td><code>model</code></td>
<td>Content Model, e.g. wikitext</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>format</code></td>
<td>Text format, e.g. text/x-wiki</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>size</code></td>
<td>The page size in bytes.</td>
<td>INTEGER</td>
</tr>
<tr>
<td><code>sha1</code></td>
<td>Revision commit hash.</td>
<td>TEXT</td>
</tr>
<tr>
<td><code>text</code></td>
<td>Unrendered wikitext.</td>
<td>TEXT</td>
</tr>
</table>

### Porting into XML

You can also use this tool to include/exclude a selection of pages from your MediaWiki XML dump. For example, you might want to exclude pages with the namespace `4773` which was used by a proprietary MediaWiki extension from your XML file. In such a case, you can run `get_wikipages(options=["page_xml"])` to partition your XML dump, then run the following to convert your pages back to XML:

```py
from export_xml import export_xml

export_xml(

  # The database file that is created by get_wikipages(...)
  sql_db_path="/path/to/sqlite/file.db",

  # Your recreated XML files will be put in this folder
  output_directory="/folder/path",
  
  # This defines the XML definitions. You might want to change this if you had used another XML schema, e.g. 0.10.
  root_xml_head="""<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.mediawiki.org/xml/export-0.11/ http://www.mediawiki.org/xml/export-0.11.xsd" version="0.11" xml:lang="en">""",

  # This simply maps the namespaces defined in the XML dump. Change to what is applicable to your wiki. 
  siteinfo_xml="""
  <siteinfo>
    <sitename>Foobar Wiki</sitename>
    <dbname>somewiki</dbname>
    <base>https://some/url</base>
    <generator>MediaWiki n.xx.yyy</generator>
    <case>first-letter</case>
    <namespaces>
      <namespace key="-2" case="first-letter">Media</namespace>
      <namespace key="-1" case="first-letter">Special</namespace>
      <namespace key="0" case="first-letter" />
      <namespace key="1" case="first-letter">Talk</namespace>
      ...
    </namespaces>
  </siteinfo>
  """",

  # Sets the filters. You can omit any if necessary.
  include_pageids=[...],
  exclude_pageids=[...],
  include_namespaces=[...],
  exclude_namespaces=[...],

  # Set this as one of the following: "only_non_redirects", "only_redirects", "all" (default: "all")
  export=...
)
```

## Limitations
 - SQLITE has a default limit of 1,000,000 bytes (approximately 1GB) that may be stored within a field. This limit may be raised to a maximum of 2,147,483,645 bytes (approximately 2 GB). Right now, this package does not have a way of chunking a wikipage's history into smaller segments in the event that the limit is exceeded. Therefore, there is a possibility that running `get_wikipages(options=["page_xml"])` may fail for pages that have a history bytesize exceeding this cap.