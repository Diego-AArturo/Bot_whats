import sys
import requests
import json
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
import threading

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
              Responde de forma cordiar y servicial, como el asesor de la empresa "Billo's".
              el menu del restaurante esta en ```{menu_Hamburguesas,menu_perros}```, habla del menu solo si el cliente pregunta por el,
              como asesor de servicio al cliente debes preguntarle al cliente, el medio de pago (efectivo, tarjeta o transferencia) con el que pagara su pedido, 
              de ser transferencia dile que lo envie a la cuenta de nequi +57 666666666. Al finalizar el pedido debes rectificar que el cliente no quiera nada más
              y darle un resumen de su pedido rectificando asi la orden,luego debes pedir la direccion de envio y un número de contacto. En caso de que el cliente
              pida reclamar su pedido en la tienda dile que hay una cede en las mercedes y otra en la 28.
              Al finalizar el pedio envia un formato ".JSON" de la siguiente manera: 

              
                
              {
               'Nombre' : Nombre del cliente,
               'productos': "Producto1", "Producto2", "Producto3" ,
               'cantidad' : "2","1","3",
               'Descripcion: "una de producto1 sin piña"," ", "sin salsas",
               'Telefono' : Telefono del cliente
               'Direccion' : Diereccion 
               'Forma de pago': medio de pago
              }
              
                 '''   )

model = genai.GenerativeModel(
    "models/gemini-1.5-flash", system_instruction=instruction
)
#print(response.text)
chat = model.start_chat()

class WhatsAppChatbot:
    def __init__(self, chat_model, send_function, message_interval=5.0):
        self.chat_model = chat_model
        self.send_function = send_function
        self.message_buffer = []
        self.timer = None
        self.lock = threading.Lock()
        self.message_interval = message_interval
        self.recibos = []

    def receive_message(self, message, number, message_id, name):
        with self.lock:
            self.message_buffer.append((message, number, message_id, name))
            if self.timer is None:
                self.start_timer()

    def start_timer(self):
        self.timer = threading.Timer(self.message_interval, self.process_messages)
        self.timer.start()

    def process_messages(self):
        with self.lock:
            if not self.message_buffer:
                return

            # Combina todos los mensajes acumulados en uno solo
            combined_message = " ".join([msg[0] for msg in self.message_buffer])
            number = self.message_buffer[0][1]  # Usamos el número del primer mensaje
            message_id = self.message_buffer[0][2]
            name = self.message_buffer[0][3]

            recibo_json = None
            try:
                # Genera la respuesta usando el modelo LLM
                response = self.chat_model.send_message(combined_message)
                response_text = response.text
                if '{' in response_text:
                    the_dict = dict(response_text[response_text.index('{'):response_text.index('}')])
                    # response_text_parts = response_text.split('{', 1)
                    # response_text = response_text_parts[0].strip()
                    # recibo_json = "{" + response_text_parts[1].strip()
                    sys.stdout('THE DICT: ', the_dict)
                    self.recibos.append(the_dict)
            except Exception as e:
                response_text = "Lo siento, no puedo procesar tu solicitud en este momento."
            finally:
                # Envía la respuesta combinada
                data = text_Message(number, response_text)
                self.send_function(data)

                # Limpiar el buffer y resetear el temporizador
                self.message_buffer = []
                self.timer = None
            
    def obtener_recibos(self):
        return self.recibos        


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

# def buttonReply_Message(number, options, body, footer, sedd,messageId):
#     buttons = []
#     for i, option in enumerate(options):
#         buttons.append(
#             {
#                 "type": "reply",
#                 "reply": {
#                     "id": sedd + "_btn_" + str(i+1),
#                     "title": option
#                 }
#             }
#         )

#     data = json.dumps(
#         {
#             "messaging_product": "whatsapp",
#             "recipient_type": "individual",
#             "to": number,
#             "type": "interactive",
#             "interactive": {
#                 "type": "button",
#                 "body": {
#                     "text": body
#                 },
#                 "footer": {
#                     "text": footer
#                 },
#                 "action": {
#                     "buttons": buttons
#                 }
#             }
#         }
#     )
#     return data

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

whatsapp_chatbot = WhatsAppChatbot(chat, enviar_Mensaje_whatsapp)

def administrar_chatbot(textu, number, messageId, name):
    textu = textu.lower()  # mensaje que envío el usuario

    print("mensaje del usuario: ", textu)
    whatsapp_chatbot.receive_message(textu, number, messageId, name)

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