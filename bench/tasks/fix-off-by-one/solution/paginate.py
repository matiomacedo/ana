def page_slice(items, page, per_page):
    """Return the items for a 1-based page number."""
    start = (page - 1) * per_page
    return items[start : start + per_page]
