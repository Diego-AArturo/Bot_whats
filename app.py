from flask import Flask, request, jsonify
import services
from dotenv import load_dotenv
import os

load_dotenv()

token_v = os.getenv('token')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Diccionario para manejar las sesiones de los usuarios
users_sessions = {}

chatbot = services.WhatsAppChatbot(chat_model=services.chat, send_function=services.enviar_Mensaje_whatsapp)

@app.route('/pedidos', methods=['GET'])
def pedidos():
    recibos = chatbot.obtener_recibos()  # Obtener los recibos almacenados
    return jsonify(recibos)  # Devolver los recibos como JSON

@app.route('/webhook', methods=['GET'])
def verificar_token():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == token_v and challenge is not None:
        return challenge
    return 'token incorrecto', 403

@app.route('/webhook', methods=['POST'])
def recibir_mensajes():
    try:
        body = request.get_json()
        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        message = value['messages'][0]
        number = services.replace_start(message['from'])  # Identificador único del usuario
        messageId = message['id']
        contacts = value['contacts'][0]
        name = contacts['profile']['name']
        text = services.obtener_Mensaje_whatsapp(message)

        # Crear nueva sesión si no existe
        if number not in users_sessions:
            users_sessions[number] = {
                'session': services.create_new_session(number),
                'chat_session': services.start_new_chat_session()  # Aquí creamos una nueva sesión de chat
            }

        # Procesa el mensaje usando el chatbot, pasando la sesión correspondiente del usuario
        chatbot_response = services.administrar_chatbot(
            text, 
            number, 
            messageId, 
            name, 
            session=users_sessions[number]['session'],
            chat_session=users_sessions[number]['chat_session']  # Pasamos la sesión de chat
        )

        return 'enviado'
    except Exception as e:
        return f'no enviado: {str(e)}'

if __name__ == '__main__':
    print('Escuchando en el puerto 5000...')
    app.run(host='0.0.0.0', port=5000, debug=True)

