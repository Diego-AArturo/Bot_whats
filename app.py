from flask import Flask, request
from flask_socketio import SocketIO, emit
import services
from dotenv import load_dotenv
import os

load_dotenv()

token_v = os.getenv('token')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/bienvenido', methods=['GET'])
def bienvenido():
    return 'Hola mundo bigdateros, desde Flask'

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

@app.route('/webhook', methods=['POST'])
def recibir_mensajes():
    try:
        body = request.get_json()
        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        message = value['messages'][0]
        number = services.replace_start(message['from'])
        messageId = message['id']
        contacts = value['contacts'][0]
        name = contacts['profile']['name']
        text = services.obtener_Mensaje_whatsapp(message)

        services.administrar_chatbot(text, number, messageId, name)
        return 'enviado'
    except Exception as e:
        return 'no enviado ' + str(e)

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')
    emit('response', {'data': 'Conexión establecida'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('message')
def handle_message(data):
    print(f'Mensaje recibido: {data}')
    emit('response', {'data': 'Mensaje recibido'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
