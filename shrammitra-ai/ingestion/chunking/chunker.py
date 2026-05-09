"""
Text chunking strategies for RAG document preparation.

Splits large documents into semantically coherent chunks optimized for:
- Elasticsearch indexing
- Jina v5 embedding (max 8192 tokens)
- Context window fit (max ~3000 tokens per chunk for RAG)

Uses a sliding window with overlap to preserve context across chunk boundaries.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DocumentChunk:
    """A single chunk of a document ready for embedding and indexing."""
    content: str
    chunk_index: int
    total_chunks: int
    title: str
    source_url: str
    source_type: str
    language: str
    act_name: Optional[str] = None
    section: Optional[str] = None
    doc_hash: str = ""


class TextChunker:
    """
    Recursive character text splitter with overlap.

    Strategy:
    1. First try to split on paragraph boundaries (\n\n)
    2. Then on sentence boundaries (. / ? / !)
    3. Then on newlines
    4. Finally on whitespace

    This preserves semantic coherence in legal text.
    """

    def __init__(
        self,
        chunk_size: int = 800,        # Target characters per chunk
        chunk_overlap: int = 150,      # Overlap between adjacent chunks
        min_chunk_size: int = 100,     # Discard chunks smaller than this
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_document(
        self,
        content: str,
        title: str,
        source_url: str,
        source_type: str = "website",
        language: str = "en",
        act_name: Optional[str] = None,
        doc_hash: str = "",
    ) -> List[DocumentChunk]:
        """
        Split a document into overlapping chunks.

        Returns list of DocumentChunk objects ready for embedding.
        """
        if not content or not content.strip():
            return []

        raw_chunks = self._split_text(content)
        # Filter out chunks that are too short
        raw_chunks = [c for c in raw_chunks if len(c.strip()) >= self.min_chunk_size]

        total = len(raw_chunks)
        chunks = []

        for i, chunk_text in enumerate(raw_chunks):
            # Extract section reference if present in chunk
            section = self._extract_section(chunk_text)

            chunks.append(
                DocumentChunk(
                    content=chunk_text.strip(),
                    chunk_index=i,
                    total_chunks=total,
                    title=title,
                    source_url=source_url,
                    source_type=source_type,
                    language=language,
                    act_name=act_name,
                    section=section,
                    doc_hash=doc_hash,
                )
            )

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Recursively split text using a hierarchy of separators."""
        separators = ["\n\n", "\n", ". ", "! ", "? ", " "]
        return self._recursive_split(text, separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Recursive splitting with overlap."""
        if not separators:
            return self._split_by_size(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        splits = text.split(separator)

        chunks: List[str] = []
        current_chunk = ""

        for split in splits:
            piece = split + (separator if separator != " " else " ")
            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap from end of previous
                if len(piece) > self.chunk_size and remaining_separators:
                    # Recurse for large pieces
                    sub_chunks = self._recursive_split(piece, remaining_separators)
                    if chunks and sub_chunks:
                        # Add overlap
                        overlap = chunks[-1][-self.chunk_overlap:]
                        sub_chunks[0] = overlap + " " + sub_chunks[0]
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    # Add overlap from previous chunk
                    overlap = current_chunk[-self.chunk_overlap:] if current_chunk else ""
                    current_chunk = overlap + " " + piece if overlap else piece

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_size(self, text: str) -> List[str]:
        """Hard split by character size as last resort."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.chunk_overlap
        return chunks

    def _extract_section(self, text: str) -> Optional[str]:
        """Extract section/rule references from text for metadata."""
        patterns = [
            r"Section\s+(\d+[A-Z]?(?:\(\d+\))?)",
            r"Rule\s+(\d+[A-Z]?)",
            r"Schedule\s+([IVXLCDM]+|\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)[:64]
        return None
