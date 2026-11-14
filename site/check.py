"""Fail the Pages build if dashboard navigation or local assets are broken."""
from html.parser import HTMLParser
from pathlib import Path


class DashboardCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])


page = Path("site/index.html")
parser = DashboardCheck()
parser.feed(page.read_text(encoding="utf-8"))
missing = [link[1:] for link in parser.links if link.startswith("#") and link[1:] not in parser.ids]
assert not missing, f"Broken in-page anchors: {missing}"
for asset in ("site/styles.css", "site/app.js"):
    assert Path(asset).is_file(), f"Missing local asset: {asset}"
print(f"Validated {len(parser.ids)} IDs, {len(parser.links)} links, and local assets")
