import logging
import sys
import requests
import json
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
import threading
import re
from test_db import insert_order
#process_messages
# import app

load_dotenv()

api = os.getenv('api_gemini')
genai.configure(api_key=api)

menu_Hamburguesas = [
    { 'Producto': 'Hamburguesa tradicional', 
    'Precio': '17.000' ,
    'Descripcion': 'Carne tradicional, tocineta, jamon, queso, piña en cuadros',
    'Disponibilidad': 'si' },
    { 'Producto': 'Hamburguesa casera', 
    'Precio': '15.000' ,
    'Descripcion':'',
    'Disponibilidad': 'si' },
    { 'Producto': 'Hamburguesa clasica angus', 
    'Precio': '17.000' ,
    'Descripcion':'',
    'Disponibilidad': 'si' },
    
    ]
menu_perros = [
    { 'Producto': 'Especial', 
    'Precio': '14.000' ,
    'Descripcion': '',
    'Disponibilidad': 'si' },
    { 'Producto': 'super', 
    'Precio': '15.000' ,
    'Descripcion': ' ',
    'Disponibilidad': 'si' },
]
instruction = ('''
Eres un asesor de servicio al cliente de una empresa de comida rápida llamada "Billo's".
Responde de forma cordial, servicial y puntual.

Para concretar un pedido necesitas: nombre, productos, cantidades de cada producto, teléfono del cliente, dirección y método de pago.

Al iniciar la conversación con el cliente, indícale que necesitas: su nombre, productos que desea, teléfono, dirección y método de pago.

Si el cliente va enviando progresivamente la información ve solicitando lo que necesites para concretar el pedido.

Utiliza como menú del restaurante la siguiente información:

Hamburguesas.
1. Hamburguesa tradicional.
Receta: Carne tradicional, tocineta, jamón, queso, piña en cuadros.
Precio: 17.000.

2. Hamburguesa casera.
Precio: 15.000.

3. Hamburguesa clásica Angus.
Precio: 17.000.

Perros.
1. Especial.
Precio: 14.000.

2. Super.
Precio: 15.000.

Si el cliente pregunta por algo que no esté en el menú, infórmale no está disponible.

Si el cliente pagará por transferencia, indícale que debe enviarla a la cuenta de Nequi +57666666666.

Si el cliente envía su dirección no preguntes si lo recogerá en el local, de lo contrario infórmale que hay una sede en Las Mercedes y otra en la calle 28.

Si identificas que el cliente ha finalizado su pedido envia un resumen e informale que se iniciará la preparación.

Además, finalizado el pedido responde el resumen con formato JSON de la siguiente forma:

{
  "name"
  "products"
  "quantity"
  "description"
  "phone"
  "address"
  "cedula"
  "email"
  "payment_method"  
}

Donde "name" tendrá como valor el nombre del cliente.
Donde "products" será un arreglo del nombre de cada producto solicitado por el cliente, donde los nombres de los productos no se deben repetir.
Donde "quantity" será un arreglo con la cantidad de cada producto solicitado.
Donde "description" será un texto de las especificaciones del cliente (Ejemplo: Hamburguesa sin salsas, Hamburguesa sin tomate, Lo recogeré en el local, etc.).
Donde "phone" será un texto del número de contacto asociado al cliente para notificar.
Donde "address" será un texto de la dirección del cliente en caso de que desee que se envíe a su casa.
Donde "cedula" será un número de identificacion del cliente.
Donde "email" será un texto 
Donde "payment_method" será un texto entre efectivo, tarjeta o transferencia.

Sin embargo, ten en cuenta que tu respuesta está siendo procesada en una API, por lo que nunca indiques por aparte que se le enviará un JSON puntualmente al usuario, es decir,
envía el JSON sin mencionar que lo vas a hacer y ya.
'''   )

model = genai.GenerativeModel(
    "models/gemini-1.5-flash", system_instruction=instruction
)
def start_new_chat_session():
    return model.start_chat()

# def create_new_session(number):
#     session = {
#         'number': number,
#         'messages': [],  # Puedes almacenar los mensajes si es necesario
#         'state': 'new',  # Estado inicial
#         'timestamp': time.time()  # Marca de tiempo de la sesión
#     }
#     print(f"Sesión creada para el número {number}: {session}")
#     return session

#print(response.text)

recibos = []
class WhatsAppChatbot:
    def __init__(self, send_function, message_interval=5.0):
        self.send_function = send_function
        self.message_buffer = []
        self.timer = None
        self.lock = threading.Lock()
        self.message_interval = message_interval

    def receive_message(self, message, number, message_id, name, chat_session):
        with self.lock:
            self.message_buffer.append((message, number, message_id, name, chat_session))
            if self.timer is None:
                self.start_timer()

    def start_timer(self):
        self.timer = threading.Timer(self.message_interval, self.process_messages)
        self.timer.start()

    def process_messages(self):
        with self.lock:
            if not self.message_buffer:
                return

            combined_message = " ".join([msg[0] for msg in self.message_buffer])
            number = self.message_buffer[0][1]
            message_id = self.message_buffer[0][2]
            name = self.message_buffer[0][3]
            chat_session = self.message_buffer[0][4]

            recibo_json = None
            try:
                response = chat_session.send_message(combined_message)
                response_text = response.text
                

                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    json_string = json_match.group(0)
                    json_string = json_string.replace(",]", "]").replace(",}", "}")

                    try:
                        recibo_json = json.loads(json_string)
                        
                        # print('JSON generado:', recibo_json)
                    
                    except json.JSONDecodeError as e:
                        logging.error(f"Error al decodificar JSON: {e}")
                        recibo_json = None

                    if recibo_json:
                        recibos.append(recibo_json)
                        print('recibo_json: ',recibo_json)
                        insert_order(recibo_json)
                        # print('Recibo almacenado en recibos:', recibos)
                        
                    response_text = response_text.replace(json_string, "").strip()
                else:
                    
                    print('No se encontró un JSON válido en la respuesta:', response_text)
            
            except Exception as e:
                logging.error(f"Error al procesar el mensaje: {e}")
                response_text = "Lo siento, no puedo procesar tu solicitud en este momento."
            finally:
                data = text_Message(number, response_text)
                self.send_function(data)

            self.message_buffer = []
            self.timer = None
            print("Finalizado el proceso de mensajes. Recibos actuales:", recibos)

    def obtener_recibos(self):
        with self.lock:
            # print('obt_recibos: ', recibos)
            return recibos


# Instancia de la clase

def obtener_Mensaje_whatsapp(message):
    if 'type' not in message :
        text = 'mensaje no reconocido'
        return text

    typeMessage = message['type']
    if typeMessage == 'text':
        text = message['text']['body']
    elif typeMessage == 'button':
        text = message['button']['text']
    elif typeMessage == 'interactive' and message['interactive']['type'] == 'list_reply':
        text = message['interactive']['list_reply']['title']
    elif typeMessage == 'interactive' and message['interactive']['type'] == 'button_reply':
        text = message['interactive']['button_reply']['title']
    else:
        text = 'mensaje no procesado'
    
    
    return text

def enviar_Mensaje_whatsapp(data):
    try:
        whatsapp_token = os.getenv('whatsapp_token')
        whatsapp_url = os.getenv('whatsapp_url')
        headers = {'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + whatsapp_token}
        print("se envia ", data)
        response = requests.post(whatsapp_url, 
                                headers=headers, 
                                data=data)
        
        if response.status_code == 200:
            return 'mensaje enviado', 200
        else:
            return 'error al enviar mensaje', response.status_code
    except Exception as e:
        return e,403
    
def text_Message(number,text):
    data = json.dumps(
            {
                "messaging_product": "whatsapp",    
                "recipient_type": "individual",
                "to": number,
                "type": "text",
                "text": {
                    "body": text
                }
            }
    )
    return data


def listReply_Message(number, options, body, footer, sedd,messageId):
    rows = []
    for i, option in enumerate(options):
        rows.append(
            {
                "id": sedd + "_row_" + str(i+1),
                "title": option,
                "description": ""
            }
        )

    data = json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {
                    "text": body
                },
                "footer": {
                    "text": footer
                },
                "action": {
                    "button": "Ver Opciones",
                    "sections": [
                        {
                            "title": "Secciones",
                            "rows": rows
                        }
                    ]
                }
            }
        }
    )
    return data

def markRead_Message(messageId):
    data = json.dumps(
        {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id":  messageId
        }
    )
    return data

def catalogo_Message(number):
    data = json.dumps(
        {
  "messaging_product": "whatsapp",
  "recipient_type": "individual",
  "to": number,
  "type": "interactive",
  "interactive": {
    "type": "catalog_message",
    "body": {
      "text": "Hello! Thanks for your interest. Ordering is easy. Just visit our catalog and add items to purchase."
    },
    "action": {
      "name": "catalog_message",
      "parameters": {
        "thumbnail_product_retailer_id": "2lc20305pt"
      }
    },
    "footer": {
      "text": "Best grocery deals on WhatsApp!"
            }
        }
        }
    )
    return data

def administrar_chatbot(textu, number, messageId, name, chat_session,chatbot):
    textu = textu.lower()
    print(f"Mensaje del usuario {number}: {textu}")
    chatbot.receive_message(textu, number, messageId, name, chat_session)

    # Marca el mensaje como leído
    markRead = markRead_Message(messageId)
    enviar_Mensaje_whatsapp(markRead)

#al parecer para mexico, whatsapp agrega 521 como prefijo en lugar de 52,
# este codigo soluciona ese inconveniente.
def replace_start(s):
    number = s[3:]
    if s.startswith("521"):
        return "52" + number
    elif s.startswith("549"):
        return "54" + number
    else:
        return s