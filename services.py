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
instruction = ('''Eres un asesor de servicio al cliente de una empresa de comida rapida llamada "Billo's", al iniciar conversacion con el cliente pide su nombre.
              Responde de forma cordiar, servicial y puntual, como el asesor de la empresa "Billo's".
              Toma el menu del restaurante solo de esta informacion ```{menu_Hamburguesas,menu_perros}```, si el cliente pregunta por algo que no este en el meno, 
               dile que no hay, habla del menu solo si el cliente pregunta por el.
              Como asesor de servicio al cliente debes preguntarle al cliente el medio de pago (efectivo, tarjeta o transferencia) con el que pagara su pedido, 
              de ser transferencia dile que lo envie a la cuenta de nequi +57 666666666. Al finalizar el pedido debes rectificar que el cliente no quiera nada más,
               luego debes pedir la direccion de envio y un número de contacto. En caso de que el cliente pida reclamar su pedido en la tienda dile que hay una cede en las mercedes y otra en la 28.
              Al finalizar el pedido pidele confirmacion al cliente, hazle un resumen de su pedido y preguntale si esta correcto.
               
               Solo Despues de que el cliente confirme el pedido eviale el siguiente mensaje:               
               Gracias por pedir a billo's                
              {"Nombre" : "Nombre del cliente",
               "productos": ["Producto1", "Producto2", "Producto3"],
               "cantidad" : ["2","1","3"],
               "Descripcion": ["una de producto1 sin piña"," ", "sin salsas"],
               "Telefono" : "Telefono del cliente",
               "Direccion" : "Direccion",
               "Forma de pago": "medio de pago"}
              
                 '''   )

model = genai.GenerativeModel(
    "models/gemini-1.5-flash", system_instruction=instruction
)
def start_new_chat_session():
    return model.start_chat()

def create_new_session(number):
    session = {
        'number': number,
        'messages': [],  # Puedes almacenar los mensajes si es necesario
        'state': 'new',  # Estado inicial
        'timestamp': time.time()  # Marca de tiempo de la sesión
    }
    print(f"Sesión creada para el número {number}: {session}")
    return session

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
                print('Response text:', response_text)

                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    json_string = json_match.group(0)
                    json_string = json_string.replace(",]", "]").replace(",}", "}")

                    try:
                        recibo_json = json.loads(json_string)
                        print('JSON generado:', recibo_json)
                    except json.JSONDecodeError as e:
                        logging.error(f"Error al decodificar JSON: {e}")
                        recibo_json = None

                    if recibo_json:
                        recibos.append(recibo_json)
                        print('Recibo almacenado en recibos:', recibos)
                        
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
            print('obt_recibos: ', recibos)
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

def administrar_chatbot(textu, number, messageId, name, session, chat_session):
    textu = textu.lower()
    print(f"Mensaje del usuario {number}: {textu}")
    WhatsAppChatbot.receive_message(textu, number, messageId, name, chat_session)

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