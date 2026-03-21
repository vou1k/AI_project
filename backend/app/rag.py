"""
RAG (Retrieval-Augmented Generation) для анализа требований.
Разбиваем текст на чанки, индексируем в векторную БД и ищем релевантные части.
"""

import os
import hashlib
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import uuid

class RequirementsRAG:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vectorstore = None
        self._init_vectorstore()

    def _init_vectorstore(self):
        if os.path.exists(self.persist_directory):
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        else:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

    def add_requirements(self, requirements_text: str, metadata: Dict = None) -> List[str]:
        """Разбить текст требований на чанки и добавить в БД"""
        docs = self.text_splitter.create_documents(
            [requirements_text],
            metadatas=[metadata or {"source": "requirements"}]
        )
        # Добавляем уникальные ID для каждого чанка
        ids = [str(uuid.uuid4()) for _ in docs]
        self.vectorstore.add_documents(docs, ids=ids)
        return ids

    def retrieve_relevant(self, query: str, k: int = 3) -> List[str]:
        """Найти наиболее релевантные чанки для запроса"""
        if not self.vectorstore:
            return []
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]

    def clear(self):
        """Очистить базу"""
        if self.vectorstore:
            self.vectorstore.delete_collection()
            self._init_vectorstore()