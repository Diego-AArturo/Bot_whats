from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import services
from dotenv import load_dotenv
import os
import eventlet
import time

load_dotenv()

token_v = os.getenv('token')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')  # Configura SocketIO para usar eventlet

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Billo\'s, comidas rapidas'

chatbot = services.WhatsAppChatbot(chat_model=services.chat, send_function=services.enviar_Mensaje_whatsapp)



@app.route('/pedidos', methods=['GET'])
def pedidos():
    time.sleep(1)  # Espera un segundo para asegurar que el proceso de mensajes ha terminado
    recibos = chatbot.obtener_recibos()  # Obtener los recibos almacenados
    return jsonify(recibos)  # Devolver los recibos como JSON


@app.route('/webhook', methods=['GET'])
def verificar_token():
    try:
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        print(token, challenge)
        if token == token_v and challenge is not None:
            return challenge
        else:
            return 'token incorrecto', 403
    except Exception as e:
        return str(e), 403


users_sessions = {}

@app.route('/webhook', methods=['POST'])
def recibir_mensajes():
    try:
        body = request.get_json()
        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        message = value['messages'][0]
        number = services.replace_start(message['from'])  # Identificador único
        messageId = message['id']
        contacts = value['contacts'][0]
        name = contacts['profile']['name']
        text = services.obtener_Mensaje_whatsapp(message)

        if number not in users_sessions:
            users_sessions[number] = services.create_new_session(number)

        # Procesa el mensaje usando el chatbot
        chatbot_response = services.administrar_chatbot(text, number, messageId, name, session=users_sessions[number])
        
        # Emitir el mensaje a través de SocketIO
        socketio.emit('response', {'data': chatbot_response}, room=number)

        return 'enviado'
    except Exception as e:
        return 'no enviado ' + str(e)



# @app.route('/webhook', methods=['POST'])
# def recibir_mensajes():
#     try:
#         body = request.get_json()
#         entry = body['entry'][0]
#         changes = entry['changes'][0]
#         value = changes['value']
#         message = value['messages'][0]
#         number = services.replace_start(message['from'])
#         messageId = message['id']
#         contacts = value['contacts'][0]
#         name = contacts['profile']['name']
#         text = services.obtener_Mensaje_whatsapp(message)

#         services.administrar_chatbot(text, number, messageId, name)
#         return 'enviado'
#     except Exception as e:
#         return 'no enviado ' + str(e)

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')
    emit('response', {'data': 'Conexión establecida'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

# @socketio.on('message', namespace='/<user_id>')
# def handle_message(data):
#     print(f'Mensaje recibido del usuario {data["user_id"]}: {data["message"]}')
#     emit('response', {'data': 'Mensaje recibido'}, namespace=f'/{data["user_id"]}')

# @socketio.on('message', namespace='/chat')
# def handle_message(data):
#     user_id = data.get('user_id')
#     message = data.get('message')
    
#     # Procesa el mensaje
#     chatbot_response = services.administrar_chatbot(message, user_id)

#     # Envía la respuesta solo al usuario correspondiente
#     emit('response', {'data': chatbot_response}, room=user_id)
@socketio.on('message', namespace='/chat')
def handle_message(data):
    user_id = data.get('user_id')
    message = data.get('message')
    
    # Procesa el mensaje usando el chatbot
    chatbot_response = services.administrar_chatbot(message, user_id)

    # Envía la respuesta solo al usuario correspondiente
    emit('response', {'data': chatbot_response}, room=user_id)


if __name__ == '__main__':
    print('Escuchando en el puerto 5000...')
    socketio.run(app, host='0.0.0.0')  # `port` es opcional y puede ser configurado según sea necesario
