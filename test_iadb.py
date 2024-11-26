import logging
import typing_extensions as typing
import json
import google.generativeai as genai
import os
import asyncio  # Importa asyncio para manejar la ejecución asincrónica
from dotenv import load_dotenv
from test_db import get_schema, query



load_dotenv()

api = os.getenv('api_gemini')
genai.configure(api_key=api)

class Recipe(typing.TypedDict):
    sql_query: str



async def human_query_to_sql(human_query: str):
    # Obtenemos el esquema de la base de datos
    database_schema = get_schema()

    system_message = f"""
    Given the following schema, write a SQL query that retrieves the requested information. 
    Return the SQL query inside a JSON structure with the key "sql_query".
    <example>{{
        "sql_query": "SELECT nombre,disponibilidad FROM productos WHERE nombre ILIKE '%vegetariana%';"
        "original_query": "tienen hamburguesas vegetarianas ?"

        "sql_query": "SELECT nombre,disponibilidad FROM productos WHERE nombre ILIKE '%hamburguesa%';"
        "original_query": "que hamburguesas tienen ? "

        "sql_query": "SELECT precio FROM productos WHERE nombre ILIKE '%perro especial%';"
        "original_query": "cuanto cuesta un perro especial ? "
    }}
    </example>
    <schema>
    {database_schema}
    </schema>
    """
    user_message = human_query

    # Enviamos el esquema completo con la consulta al LLM
    model = genai.GenerativeModel(
        "models/gemini-1.5-flash", 
        system_instruction=system_message
    )
    response = model.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(
            temperature=0,
            response_mime_type="application/json", response_schema=list[Recipe]
        ),
    )
    rest_dict = json.loads(response.text)
    

    resp_consult = await query(rest_dict[0]['sql_query'])
    
    return resp_consult

# Ejecutar la función asincrónica en un entorno sincrónico
if __name__ == "__main__":
    user_message = 'tienen hamburguesas vegetarianas ?'
    p = asyncio.run(human_query_to_sql(user_message))
    # print('query:', p)

    model = genai.GenerativeModel(
        "models/gemini-1.5-flash", 
    )
    
    prompt = f'''
    
    respode a la pregunta teniendo en cuenta la siguiente informacion {p}
    pregunta: {user_message}

    '''
    response = model.generate_content(
        user_message,
        generation_config=genai.GenerationConfig(
            temperature=0.1,
            
        ),
    )
    print('data: ' ,p)
    print('response: ', response.text)
