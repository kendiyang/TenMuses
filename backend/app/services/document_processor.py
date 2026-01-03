"""Document Processing Service - Extract, chunk, and hash documents with advanced parsing"""
import hashlib
import logging
import re
import tiktoken
from typing import List, Tuple, Optional
from pathlib import Path
from html.parser import HTMLParser
import io

logger = logging.getLogger(__name__)


class HTMLTextExtractor(HTMLParser):
    """HTML 文本提取器"""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'meta', 'link'}
        self.skip = False
    
    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip = True
    
    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip = False
        elif tag in ['p', 'br', 'div', 'li']:
            self.text_parts.append('\n')
    
    def handle_data(self, data):
        if not self.skip:
            text = data.strip()
            if text:
                self.text_parts.append(text)
    
    def get_text(self):
        return ' '.join(self.text_parts)


class DocumentProcessor:
    """文档处理器 - 提取、分片、去重，支持多种文件格式"""
    
    # 支持的 MIME 类型映射
    SUPPORTED_TYPES = {
        "application/pdf": "pdf",
        "text/plain": "text",
        "text/markdown": "markdown",
        "text/html": "html",
        "application/x-html": "html",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    }
    
    def __init__(self, max_chunk_tokens: int = 500, overlap_tokens: int = 50):
        """
        初始化文档处理器
        
        Args:
            max_chunk_tokens: 每个分片的最大 Token 数
            overlap_tokens: 相邻分片的重叠 Token 数（用于保持上下文）
        """
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")
        logger.info(f"DocumentProcessor initialized: max_tokens={max_chunk_tokens}, overlap={overlap_tokens}")
    
    def extract_text(self, file_path: str, mime_type: str) -> str:
        """
        从文件提取纯文本内容
        
        Args:
            file_path: 文件路径
            mime_type: 文件 MIME 类型
            
        Returns:
            提取的文本内容
            
        Raises:
            ValueError: 不支持的文件类型
            Exception: 提取过程中的错误
        """
        try:
            if mime_type == "application/pdf":
                return self._extract_pdf(file_path)
            elif mime_type in ["text/plain", "text/markdown"]:
                return self._extract_text(file_path)
            elif mime_type in ["text/html", "application/x-html"]:
                return self._extract_html(file_path)
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return self._extract_docx(file_path)
            elif mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                return self._extract_pptx(file_path)
            else:
                raise ValueError(f"Unsupported file type: {mime_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def _extract_pdf(self, file_path: str) -> str:
        """提取 PDF 文本"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text_parts = []
            
            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from PDF page {page_num}: {str(e)}")
            
            result = "\n\n".join(text_parts)
            logger.debug(f"Extracted {len(result)} characters from PDF")
            return result
        except ImportError:
            raise ValueError("pypdf is required for PDF extraction. Install with: pip install pypdf")
    
    def _extract_text(self, file_path: str) -> str:
        """读取纯文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _extract_html(self, file_path: str) -> str:
        """提取 HTML 文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            extractor = HTMLTextExtractor()
            extractor.feed(html_content)
            return extractor.get_text()
        except Exception as e:
            logger.warning(f"HTML extraction error: {str(e)}, falling back to raw text")
            return self._extract_text(file_path)
    
    def _extract_docx(self, file_path: str) -> str:
        """提取 DOCX 文本"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            # 添加表格内容
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text)
            
            result = "\n\n".join(text_parts)
            logger.debug(f"Extracted {len(result)} characters from DOCX")
            return result
        except ImportError:
            raise ValueError("python-docx is required for DOCX extraction. Install with: pip install python-docx")
    
    def _extract_pptx(self, file_path: str) -> str:
        """提取 PPTX 文本"""
        try:
            from pptx import Presentation
            
            prs = Presentation(file_path)
            text_parts = []
            
            for slide_num, slide in enumerate(prs.slides):
                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text)
                
                if slide_text:
                    text_parts.append(f"[Slide {slide_num + 1}]\n" + "\n".join(slide_text))
            
            result = "\n\n".join(text_parts)
            logger.debug(f"Extracted {len(result)} characters from PPTX")
            return result
        except ImportError:
            raise ValueError("python-pptx is required for PPTX extraction. Install with: pip install python-pptx")
    
    def chunk_text(self, text: str, use_sentence_boundary: bool = True) -> List[Tuple[str, int]]:
        """
        将文本分片，不超过 max_chunk_tokens，可选句子级边界
        
        Args:
            text: 要分片的文本
            use_sentence_boundary: 是否在句子边界处分割
            
        Returns:
            [(chunk_text, token_count), ...] 列表
        """
        if not text or not isinstance(text, str):
            return []
        
        # 清理文本
        text = text.strip()
        
        # 如果整个文本都很小，直接返回
        total_tokens = len(self.encoding.encode(text))
        if total_tokens <= self.max_chunk_tokens:
            return [(text, total_tokens)]
        
        chunks = []
        
        if use_sentence_boundary:
            chunks = self._chunk_by_sentences(text)
        else:
            chunks = self._chunk_by_paragraphs(text)
        
        logger.info(f"Created {len(chunks)} chunks from text ({total_tokens} tokens)")
        return chunks
    
    def _chunk_by_paragraphs(self, text: str) -> List[Tuple[str, int]]:
        """按段落分片"""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for para in paragraphs:
            para_tokens = len(self.encoding.encode(para))
            
            # 单个段落超过限制，强制分割
            if para_tokens > self.max_chunk_tokens:
                # 先保存当前 chunk
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunk_tokens = len(self.encoding.encode(chunk_text))
                    chunks.append((chunk_text, chunk_tokens))
                    current_chunk = []
                    current_tokens = 0
                
                # 分割大段落
                sub_chunks = self._chunk_by_sentences(para)
                chunks.extend(sub_chunks)
            
            # 累积段落
            elif current_tokens + para_tokens > self.max_chunk_tokens:
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunk_tokens = len(self.encoding.encode(chunk_text))
                    chunks.append((chunk_text, chunk_tokens))
                
                current_chunk = [para]
                current_tokens = para_tokens
            else:
                current_chunk.append(para)
                current_tokens += para_tokens
        
        # 最后一个 chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunk_tokens = len(self.encoding.encode(chunk_text))
            chunks.append((chunk_text, chunk_tokens))
        
        return chunks
    
    def _chunk_by_sentences(self, text: str) -> List[Tuple[str, int]]:
        """按句子分片"""
        # 简单的句子分割器（可根据需要改进）
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sent in sentences:
            sent_tokens = len(self.encoding.encode(sent))
            
            if sent_tokens > self.max_chunk_tokens:
                # 保存当前 chunk
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunk_tokens = len(self.encoding.encode(chunk_text))
                    chunks.append((chunk_text, chunk_tokens))
                    current_chunk = []
                    current_tokens = 0
                
                # 处理超大句子（强制分割）
                words = sent.split()
                word_chunk = []
                word_tokens = 0
                
                for word in words:
                    word_token_count = len(self.encoding.encode(word))
                    if word_tokens + word_token_count > self.max_chunk_tokens:
                        if word_chunk:
                            chunk_text = " ".join(word_chunk)
                            chunk_tokens = len(self.encoding.encode(chunk_text))
                            chunks.append((chunk_text, chunk_tokens))
                            word_chunk = []
                            word_tokens = 0
                    
                    word_chunk.append(word)
                    word_tokens += word_token_count
                
                if word_chunk:
                    chunk_text = " ".join(word_chunk)
                    chunk_tokens = len(self.encoding.encode(chunk_text))
                    chunks.append((chunk_text, chunk_tokens))
            
            # 累积句子
            elif current_tokens + sent_tokens > self.max_chunk_tokens:
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunk_tokens = len(self.encoding.encode(chunk_text))
                    chunks.append((chunk_text, chunk_tokens))
                
                current_chunk = [sent]
                current_tokens = sent_tokens
            else:
                current_chunk.append(sent)
                current_tokens += sent_tokens
        
        # 最后一个 chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk_tokens = len(self.encoding.encode(chunk_text))
            chunks.append((chunk_text, chunk_tokens))
        
        return chunks
    
    def compute_hash(self, content: str) -> str:
        """
        计算内容 SHA256 哈希（用于去重）
        
        Args:
            content: 内容文本
            
        Returns:
            SHA256 哈希值
        """
        if not isinstance(content, str):
            content = str(content)
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_token_count(self, text: str) -> int:
        """获取文本的 Token 数量"""
        if not isinstance(text, str):
            return 0
        return len(self.encoding.encode(text))
