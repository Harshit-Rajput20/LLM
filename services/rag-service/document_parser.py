"""Document parser supporting PDF, TXT, MD, DOCX formats."""

import os
from typing import List, Dict
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup
import re


class DocumentParser:
    """Parses various document formats into clean text."""
    
    @staticmethod
    def parse_pdf(file_content: bytes, filename: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(file_content)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            return DocumentParser._clean_text(text)
        except Exception as e:
            print(f"PDF parsing error: {e}")
            return ""
    
    @staticmethod
    def parse_txt(file_content: bytes, filename: str) -> str:
        """Extract text from TXT file."""
        return DocumentParser._clean_text(file_content.decode('utf-8', errors='ignore'))
    
    @staticmethod
    def parse_md(file_content: bytes, filename: str) -> str:
        """Extract text from Markdown file (strip markdown syntax)."""
        text = file_content.decode('utf-8', errors='ignore')
        # Basic markdown stripping
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*\*(.*?)\*\*|\*(.*?)\*', r'\1\2', text)
        return DocumentParser._clean_text(text)
    
    @staticmethod
    def parse_docx(file_content: bytes, filename: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_content)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return DocumentParser._clean_text(text)
        except Exception as e:
            print(f"DOCX parsing error: {e}")
            return ""
    
    @staticmethod
    def parse(filename: str, file_content: bytes) -> str:
        """Parse document based on file extension."""
        ext = os.path.splitext(filename.lower())[1]
        
        if ext == '.pdf':
            return DocumentParser.parse_pdf(file_content, filename)
        elif ext == '.txt':
            return DocumentParser.parse_txt(file_content, filename)
        elif ext in ['.md', '.markdown']:
            return DocumentParser.parse_md(file_content, filename)
        elif ext == '.docx':
            return DocumentParser.parse_docx(file_content, filename)
        else:
            # Default to text parsing
            return DocumentParser.parse_txt(file_content, filename)
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = text.strip()
        
        return text

