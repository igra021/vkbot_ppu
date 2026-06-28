# llm\rag.py 
# функции работы с RAG

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
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
        self.db = None
        self._build_index(file_path)


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
                        "object": row["Объект"],
                        "answer": row["Ответ"]
                    }
                )
                documents.append(doc)
            db = FAISS.from_documents(documents, self.embeddings)
            return db

        except Exception as e:
            logger.error(f"Ошибка: {e}. Файл XLSX: {file_path}")
            raise

    def search(self, query: str, object_type: str = None, top_k: int=5) -> list:
        """
        Поиск чанков по запросу query и типу объекта object_type
        Args:
            query: Запрос пользователя
            object_type: Фильтр по объекту утепления (чердак/стены/пол)
            top_k: Количество результатов
        Returns:
            list: Найденные документы с метаданными
        """

        try:
            filter_param = {}
            if object_type:
                filter_param['object'] = object_type
                logger.debug(f"🔍 Поиск с фильтром: object={object_type}")
            results = self.db.similarity_search(
                query,
                filter=filter_param,  # ← здесь используется metadata
                k=top_k
            )
            return results
        
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return []

    def get_answer(self, query: str, object_type) -> str:
        """
        Получить ответ на вопрос
        """ 

        # 2. Ищем похожие чанки
        results = self.search(query, object_type)
        
        if not results:
            return "К сожалению, я не нашел информации по вашему вопросу."
        
        # 3. Берём самый релевантный ответ
        best = results[0]
        return best.metadata.get('answer', best.page_content)
    
   
