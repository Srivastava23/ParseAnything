from parseanything.cli.export import document_to_markdown

def to_markdown(doc, include_ids: bool = True) -> str:
    """
    Renders a Document model into structured Markdown with provenance and confidence annotations.
    """
    return document_to_markdown(doc, include_ids=include_ids)
