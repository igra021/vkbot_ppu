# llm\rag.py 
# функции работы с RAG

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import pandas as pd, re
from loguru import logger
from init.config import api_key, embeddings_model, base_url

class RAGSystem:
    """
    Args: csv_path: Путь к XLSX с базой знаний
    """
        
    def __init__(self, file_path: str):
        self.embeddings = OpenAIEmbeddings(
            model=embeddings_model,
            openai_api_base=base_url,
            openai_api_key=api_key
        )
        # Пытаемся создать индекс, но не падаем при ошибке
        self.db = None
        try:
            self.db = self._build_index(file_path)
            if self.db:
                logger.info(f"✅ RAGSystem инициализирован. Документов: {self.db.index.ntotal}")
            else:
                logger.warning("⚠️ RAGSystem инициализирован без базы данных (db = None)")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации RAGSystem: {e}")
            self.db = None


    def _build_index(self, file_path):
        """Создаёт индекс из XLSX"""        
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            questions = df['Вопрос'].astype(str).tolist()
            answers = df['Ответ'].astype(str).tolist()
            documents = []
            for q, a in zip(questions, answers):
                text = f"Вопрос: {q}\nОтвет: {a}"
                doc = Document(page_content=text, metadata={"question": q, "answer": a})
                documents.append(doc)

            db = FAISS.from_documents(documents, self.embeddings)
            logger.info(f"✅ Индекс создан: {len(documents)} документов")
            return db

        except FileNotFoundError:
            logger.error(f"❌ Файл данных для RAG не найден: {file_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Ошибка создания БД для RAG: {e}")
            raise


    def search_rag(self, query: str, k: int = 2) -> str:
        """Поиск в RAG"""
        
        logger.debug(f"⚠️ RAG запрос: '{query}'")

        # Проверка, что база данных инициализирована
        if self.db is None:
            logger.warning(f"⚠️ RAG не инициализирован. Запрос: '{query}'")
            return "Информация не найдена."
        
        docs = self.db.similarity_search(query, k=k)
        if not docs:
            logger.warning(f"⚠️ RAG Запрос: '{query}' → НИЧЕГО НЕ НАЙДЕНО")
            return "Информация не найдена."

        results = []
        for doc in docs:
            answer = doc.metadata.get("answer", doc.page_content)
            logger.debug(f"✅ RAG ответ: {answer}")
            results.append(str(answer))

        full_response = "\n---\n".join(results)
        
        return full_response


    def calculate_cost(self, area: int, material: str = "дерево", object_type: str = "мансарда") -> float:
        """Ищем цену за 1 кв.м., делаем расчет по площади"""

        price_query = f"цена утепления пенополиуретаном за квадратный метр для {object_type} из {material}"
        price_answer = self.search_rag(price_query, k=1)
        #if "не найдена" in price_answer.lower() or not price_answer.strip():
            #price_query = f"цена утепления пенополиуретаном за квадратный метр для {object_type}"
            #price_answer = self.search_rag(price_query, k=1)

        numbers = re.findall(r'\d+', price_answer.replace(',', ''))
        price_per_m2 = float(numbers[0])

        total = area * price_per_m2
        logger.debug(f"RAG Цена за м²: {price_per_m2} руб, Итого: {total} руб")
        return total              


    def is_ready(self) -> bool:
        """Проверяет, готова ли RAG к работе"""
        return self.db is not None   
        
        
