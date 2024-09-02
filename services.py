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

instruction = ("Eres un asesor de servicio al cliente de una empresa de comida rapida llamada 'Billo's', al iniciar conversacion con el cliente pide su nombre" 
              "el menu del restaurante es hamburguesas y perros calientes, donde los perros cuestan 3.000 pesos y las hamburguesas 5.000 pesos"
              "como asesor de servicio al cliente debes preguntarle al cliente, el medio de pago (efectivo, tarjeta o transferencia) con el que pagara su pedido"
              "ademas debes de rectificarle la orden al usuario y por ultimo pedir la direccion de envio y un número de contacto"
                    )

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

            # Genera la respuesta usando el modelo LLM
            response = self.chat_model.send_message(combined_message)
            response_text = response.text

            # Envía la respuesta combinada
            data = text_Message(number, response_text)
            self.send_function(data)

            # Limpiar el buffer y resetear el temporizador
            self.message_buffer = []
            self.timer = None

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

# whatsapp_chatbot = WhatsAppChatbot(chat, enviar_Mensaje_whatsapp)

# def administrar_chatbot(textu,number, messageId, name):
#     textu = textu.lower() #mensaje que envio el usuario
#     list = []
    
#     # print("mensaje del usuario: ",textu)
#     whatsapp_chatbot.receive_message(textu, number, messageId, name)

#     markRead = markRead_Message(messageId)
#     list.append(markRead)
#     time.sleep(2)
    
#     response = chat.send_message(textu)
   
#     data = text_Message(number,response.text)
#     list.append(data)
   
   
#     for item in list:
#         enviar_Mensaje_whatsapp(item)

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