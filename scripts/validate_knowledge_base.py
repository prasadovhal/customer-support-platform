"""Validate knowledge base articles — metadata, required fields, file structure."""
import os
import sys

KB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "knowledge_base")

REQUIRED_META = ["document_id","title","category","source","source_type","version","effective_from","language"]
KNOWN_CATEGORIES = ["shipping","returns","refunds","payments","products","account",
                    "troubleshooting","orders","warranty","security"]


def parse_frontmatter(content):
    meta = {}
    if not content.startswith("---"):
        return meta
    end = content.find("\n---", 3)
    if end == -1:
        return meta
    frontmatter = content[3:end].strip()
    for line in frontmatter.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


def validate():
    passed = True
    kb_dir = os.path.abspath(KB_DIR)

    if not os.path.isdir(kb_dir):
        print(f"  [FAIL] Knowledge base directory not found: {kb_dir}")
        return False

    articles = []
    for root, dirs, files in os.walk(kb_dir):
        for fn in files:
            if fn.endswith(".md"):
                articles.append(os.path.join(root, fn))

    print(f"\n[Knowledge Base] Found {len(articles)} articles in {kb_dir}")

    if len(articles) < 15:
        print(f"  [FAIL] Expected ~20+ articles, found {len(articles)}")
        passed = False
    else:
        print(f"  [PASS] Article count: {len(articles)}")

    # Validate each article
    doc_ids = []
    meta_failures = 0
    category_failures = 0
    for path in articles:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        meta = parse_frontmatter(content)

        missing = [f for f in REQUIRED_META if not meta.get(f)]
        if missing:
            print(f"  [FAIL] {os.path.basename(path)}: missing metadata: {missing}")
            meta_failures += 1
            passed = False
        else:
            did = meta.get("document_id","")
            doc_ids.append(did)
            cat = meta.get("category","")
            if cat not in KNOWN_CATEGORIES:
                category_failures += 1

    if meta_failures == 0:
        print(f"  [PASS] All articles have required metadata")

    # Uniqueness of document_ids
    if len(doc_ids) != len(set(doc_ids)):
        dupes = [d for d in set(doc_ids) if doc_ids.count(d) > 1]
        print(f"  [FAIL] Duplicate document_ids: {dupes}")
        passed = False
    else:
        print(f"  [PASS] document_id uniqueness")

    if category_failures:
        print(f"  [WARN] {category_failures} articles have unexpected category values")
    else:
        print(f"  [PASS] Category values")

    # Category distribution
    cat_dist = {}
    for path in articles:
        cat = os.path.basename(os.path.dirname(path))
        cat_dist[cat] = cat_dist.get(cat, 0) + 1
    print(f"  [INFO] Article distribution by folder: {cat_dist}")
    print(f"  [INFO] Document IDs: {sorted(doc_ids)}")
    return passed


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
