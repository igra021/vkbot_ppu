

async def parsing_answer():
    try:
            agent_command = data["Агент-аналитик"]['Имя агента']
            agent_message = data[agent_command]['Сообщение']

        # ошибка имени агента в отчете агента-аналитика
        except KeyError as e:
            logger.warning(f"❌ Ошибка в имени агента в промте: {e}")
            agents = ['Агент-выявления потребностей','Агент-консультант','Агент-презентатор','Агент-закрытия возражений','Агент-тип клиента']
            for agent in agents:    
                agent_message = data.get(agent, {}).get("Сообщение")
                if agent_message:
                    return agent_message
            return "Произошла ошибка при разборе ответа."        

        
        # 6. Если агент-консультант — пробуем RAG
        if agent_command == 'Агент-консультант':
            try: 
                data_consultant = data['Агент-консультант']
                data_query = data_consultant.get('Поисковый_запрос_RAG')
            except KeyError as e:
                logger.error(f"❌ Ошибка формирования Поискового запроса RAG в промте: {e}")
                return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"

            try:    
                if data_query and rag:
                    rag_answer = rag.search(data_query)

                    if rag_answer and rag_answer != "not_found":
                        
                        # Формируем новый запрос с RAG без system
                        history_without_system = history  
                        rag_messages = [
                            {"role": "system", "content": consultant_prompt + " " + rag_answer}
                        ]
                        rag_messages.extend(history_without_system)
                        
                        # Получаем ответ с учётом RAG
                        try:
                            rag_response = await get_answer_llm(rag_messages)
                        except Exception as e:
                            logger.error(e)
                            return "Произошла ошибка в работе RAG ЛЛМ. Повторите ваш вопрос"
                        
                        if verbose:
                            print("\n📚 Ответ RAG:", rag_response, '\n')
                        
                        try:
                            rag_data = json.loads(rag_response)
                            final_answer = rag_data.get('answer', agent_message)
                        except json.JSONDecodeError:
                            logger.error(f"LLM консультант вернул не JSON: {answer}")
                            return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"
                        
                        # Сохраняем ответ ассистента в БД
                        await save_message(user_id, "assistant", final_answer)
                        return final_answer
                    else:
                        logger.warning(f"RAG не нашел ответ на вопрос: {data_query}")
                        return "Не смог найти ответ на ваш вопрос"
            except Exception as e:
                logger.error(f"❌ Ошибка в chat_gpt: {e}")
                return "Произошла ошибка при обработке ответа. Повторите ваш вопрос"

    