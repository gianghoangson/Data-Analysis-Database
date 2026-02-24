"""
Finance38 - Trích xuất 38 chỉ số tài chính từ BCTC PDF
"""

from .db import Database, get_db, init_database
from .extract_pdf import PDFExtractor, extract_pdf, process_filings_folder
from .external import get_market_data, get_all_external_data
from .compute import compute_all_derived, validate_data
from .utils import parse_vn_number, load_mapping

__version__ = '1.0.0'
__all__ = [
    'Database',
    'get_db',
    'init_database',
    'PDFExtractor',
    'extract_pdf',
    'process_filings_folder',
    'get_market_data',
    'get_all_external_data',
    'compute_all_derived',
    'validate_data',
    'parse_vn_number',
    'load_mapping',
]
