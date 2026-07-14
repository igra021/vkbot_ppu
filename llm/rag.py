# llm\rag.py 
# функции работы с RAG

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import pandas as pd
from loguru import logger

from config import api_key, embeddings_model, base_url

class RAGSystem:
    """
    Args:
            csv_path: Путь к XLSX с базой знаний
    """
    logger.info("Инициализация RAGSystem...")
        
    def __init__(self, file_path: str = 'data/answers.xlsx'):
        self.embeddings = OpenAIEmbeddings(
            model=embeddings_model,
            openai_api_base=base_url,
            openai_api_key=api_key
        )
        # Пытаемся создать индекс, но не падаем при ошибке
        try:
            self.db = self._build_index(file_path)
            if self.db is not None:
                logger.info(f"✅ RAGSystem инициализирован. Документов: {self.db.index.ntotal}")
            else:
                logger.warning("⚠️ RAGSystem инициализирован без базы данных (db = None)")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RAGSystem: {e}")
            self.db = None


    def _build_index(self, file_path):
        """Создаёт индекс из XLSX"""        
        try:
            df = pd.read_excel(file_path,  engine='openpyxl')
            df_clean = df[df.notna().all(axis=1)]
            documents = []
            for _, row in df_clean.iterrows():
                doc = Document(
                    page_content = row["Вопрос"],
                    metadata = {
                        "answer": row["Ответ"]
                    }
                )
                documents.append(doc)
            db = FAISS.from_documents(documents, self.embeddings)
            logger.info(f"✅ Индекс создан: {len(documents)} документов")
            return db

        except Exception as e:
            logger.error(f"Ошибка: {e}. Файл XLSX: {file_path}")
            raise

    def search(self, query: str, top_k: int=1) -> list:
        """
        Поиск чанков по запросу query
        Args:
            query: Запрос пользователя
            top_k: Количество результатов
        Returns:
            list: Найденные документы с метаданными
        """

        try:       
            
            logger.info(f"RAG поступил вопрос: {query}")
            results = self.db.similarity_search(
                query,
                k=top_k
            )
            if results:
                
                # Берём самый релевантный ответ
                best = results[0]
                logger.debug('RAG найден ответ: ', best.metadata.get('answer', best.page_content))
                return best.metadata.get('answer', best.page_content)
            else:   
                return None
        
        except Exception as e:
            logger.error(f"❌ Ошибка поиска в RAG: {e}")
            return []

    def is_ready(self) -> bool:
        """Проверяет, готова ли RAG к работе"""
        return self.db is not None   
        
        

    
   
