import re
from pathlib import Path


WIKI = Path("wiki")
EXAMPLE_LINKS = {"stem", "wikilink"}


def _wiki_files():
    return sorted(WIKI.rglob("*.md"))


def test_wikilinks_resolve_by_basename():
    stems = {path.stem for path in _wiki_files()}
    broken = []
    path_links = []
    for path in _wiki_files():
        for match in re.finditer(r"\[\[([^\]]+)\]\]", path.read_text()):
            target = match.group(1).split("|", 1)[0].strip()
            if "/" in target:
                path_links.append((path, target))
            if target not in stems and target not in EXAMPLE_LINKS:
                broken.append((path, target))

    assert path_links == []
    assert broken == []


def test_markdown_pages_have_required_frontmatter():
    required = {"title", "type", "tags", "status", "last_reviewed"}
    issues = []
    for path in _wiki_files():
        text = path.read_text()
        if not text.startswith("---\n"):
            issues.append((path, "missing frontmatter"))
            continue
        end = text.find("\n---", 4)
        keys = {m.group(1) for m in re.finditer(r"^([A-Za-z_]+):", text[4:end], flags=re.M)}
        missing = sorted(required - keys)
        if missing:
            issues.append((path, ",".join(missing)))

    assert issues == []
