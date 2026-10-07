from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel
from parseanything.errors import ErrorCode, ParseError

SCHEMA_VERSION = "1.0.0"

class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FIGURE = "figure"
    CHART = "chart"
    EQUATION = "equation"
    CAPTION = "caption"
    HEADER = "header"
    FOOTER = "footer"
    FOOTNOTE = "footnote"
    CODE = "code"
    OTHER = "other"

class BBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float

class Region(BaseModel):
    bbox: BBox
    label: str
    score: float

class TableCell(BaseModel):
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    text: str
    is_header: bool = False

class TableData(BaseModel):
    n_rows: int
    n_cols: int
    cells: list[TableCell]
    header_rows: int = 0
    markdown: Optional[str] = None
    html: Optional[str] = None
    pages: list[int] = []

class Point(BaseModel):
    x: float | str
    y: float

class Series(BaseModel):
    name: str
    points: list[Point]

class ChartData(BaseModel):
    chart_type: str
    title: Optional[str] = None
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    series: list[Series] = []
    data_table_markdown: Optional[str] = None
    caption: Optional[str] = None
    values_estimated: bool = True

class Provenance(BaseModel):
    page: int
    bbox: Optional[BBox] = None
    source_type: str = ""
    extractor: str = ""
    confidence: float = 1.0

class Block(BaseModel):
    id: str
    type: BlockType
    page: int
    bbox: Optional[BBox] = None
    locator: Optional[str] = None
    content: str = ""
    level: Optional[int] = None
    table: Optional[TableData] = None
    chart: Optional[ChartData] = None
    latex: Optional[str] = None
    reading_order: int = 0
    confidence: float = 1.0
    flagged: bool = False
    flag_reason: Optional[str] = None
    source_extractor: str = ""
    meta: dict = {}
    provenance: Optional[Provenance] = None

class Page(BaseModel):
    number: int
    width: float
    height: float
    kind: Literal["digital", "scanned", "mixed", "image", "virtual"] = "digital"
    blocks: list[Block] = []

class DocStats(BaseModel):
    pages: int = 0
    blocks: int = 0
    flagged_blocks: int = 0
    elapsed_s: float = 0.0
    pages_per_sec: float = 0.0
    est_cost_usd: float = 0.0

class Document(BaseModel):
    source: str
    format: str
    pages: list[Page] = []
    errors: list[ParseError] = []
    stats: DocStats = DocStats()
    meta: dict = {}
    analysis: dict = {}
