# llm/rag.py
# функции работы с RAG

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
import pandas as pd, re
from loguru import logger
from config import api_key, embeddings_model, base_url

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


    def search_rag(self, query: str, k: int = 1) -> str:
        """Поиск в RAG"""
        
        logger.info(f"🔍 RAG ЗАПРОС: '{query}' (k={k})")

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
        logger.info(f"✅ RAG РЕЗУЛЬТАТ: найдено {len(docs)} ответов")
        
        return full_response


    def get_thickness(self, object_type: str, material: str) -> str:
        """
        Находит рекомендуемую толщину ППУ для объекта и материала.
        
        Args:
            object_type: Тип объекта (стены, пол, мансарда, ...)
            material: Материал конструкции (брус, пеноблок, ...)
        
        Returns:
            str: Толщина (например, "3 см" или "5 см")
        """
        print('1')
        # Формируем запрос для поиска толщины
        query = f"толщина утепления ППУ для {object_type} из {material}"
        logger.info(f"📏 RAG ПОИСК ТОЛЩИНЫ: '{query}'")
        result = self.search_rag(query, k=1)
        
        if result:
            logger.info(f"✅ RAG НАЙДЕНА ТОЛЩИНА: {result}")
            return result
        
        # Если не нашли, пробуем без объекта
        if material:
            query2 = f"толщина утепления ППУ для {material}"
            logger.info(f"📏 RAG ПОИСК ТОЛЩИНЫ (повторный): '{query2}'")
            result2 = self.search_rag(query2, k=1)
            if result2:
                logger.info(f"✅ RAG НАЙДЕНА ТОЛЩИНА: {result2}")
                return result2
        
        # Если ничего не найдено — возвращаем значение по умолчанию
        default_thickness = "минимальная толщина 3 см плотность 30 кг" if object_type != "мансарда" else "минимальная толщина 7 см плотность 30 кг"
        logger.warning(f"⚠️ ТОЛЩИНА НЕ НАЙДЕНА, используем: {default_thickness}")
        return default_thickness


    def get_price_by_thickness(self, thickness: str) -> float:

        """
        Находит цену за 1 кв.м. по толщине.
        
        Args:
            thickness: Толщина (например, "3 см")
        
        Returns:
            float: Цена за 1 кв.м.
        """

        print('2')
        # Формируем запрос для поиска цены по толщине
        query = f"цена утепления ППУ {thickness}"
        logger.info(f"💰 RAG ПОИСК ЦЕНЫ ПО ТОЛЩИНЕ: '{query}'")
        
        result = self.search_rag(query, k=1)
        
        # Пытаемся извлечь число из ответа
        numbers = re.findall(r'(\d+)\s*р', result)
        if numbers:
            price = float(numbers[0])
            logger.info(f"✅ RAG НАЙДЕНА ЦЕНА: {price} руб/м²")
            return price
        
        # Если не нашли, пробуем найти любое число в ответе
        numbers2 = re.findall(r'(\d+)', result.replace(',', ''))
        if numbers2:
            price = float(numbers2[0])
            logger.info(f"✅ RAG НАЙДЕНА ЦЕНА (число): {price} руб/м²")
            return price
        
        # Если ничего не найдено — возвращаем значение по умолчанию
        logger.warning(f"⚠️ RAG ЦЕНА НЕ НАЙДЕНА для толщины {thickness}, используем 1500 руб/м²")
        return 1500.0


    def calculate_cost(self, material: str, object_type: str, area: int=0) -> float:
        """
        Рассчитывает стоимость утепления:
        1. Находит толщину для объекта и материала
        2. По толщине находит цену за 1 кв.м.
        3. Умножает на площадь
        
        Args:
            area: Площадь в кв.м.
            material: Материал конструкции (по умолчанию 'дерево')
            object_type: Тип объекта (по умолчанию 'мансарда')
        
        Returns:
            float: Общая стоимость
        """
        logger.info(f"💰 CALCULATE_COST: area={area}, material='{material}', object_type='{object_type}'")
        
        # ШАГ 1: Находим толщину
        thickness = self.get_thickness(object_type, material)
        logger.debug(f"📏 ИСПОЛЬЗУЕМАЯ ТОЛЩИНА: {thickness}")
        
        # ШАГ 2: По толщине находим цену за 1 кв.м.
        price_per_m2 = self.get_price_by_thickness(thickness)
        logger.debug(f"💰 ЦЕНА ЗА М²: {price_per_m2} руб")
        
        # ШАГ 3: Рассчитываем общую стоимость
        if area:
            total = area * price_per_m2
            return total
        else:
            return price_per_m2


    def is_ready(self) -> bool:
        """Проверяет, готова ли RAG к работе"""
        return self.db is not None