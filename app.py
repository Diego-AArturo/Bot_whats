from flask import Flask, request, jsonify
import services
from dotenv import load_dotenv
import os
import test_db

load_dotenv()

token_v = os.getenv('token')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Diccionario para manejar las sesiones de los usuarios
users_sessions = {}

chatbot = services.WhatsAppChatbot(send_function=services.enviar_Mensaje_whatsapp)

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
                #'session': services.create_new_session(number),
                'chat_session': services.start_new_chat_session()  # Aquí creamos una nueva sesión de chat
            }
            # print(users_sessions[number]['chat_session'])
            print(f"Texto: {text}")
            print(f"Número: {number}")
            print(f"MessageId: {messageId}")
            print(f"Nombre: {name}")
            # print(f"Chat_session: {users_sessions[number]['chat_session']}")
            print(f"Chatbot: {chatbot}")

        # Procesa el mensaje usando el chatbot, pasando la sesión correspondiente del usuario
        chatbot_response = services.administrar_chatbot(
            text, 
            number, 
            messageId, 
            name, 
            #session=users_sessions[number]['session'],
            chat_session=users_sessions[number]['chat_session'], # Pasamos la sesión de chat
            chatbot=chatbot
        )

        return 'enviado'
    except Exception as e:
        return f'no enviado: {str(e)}'

@app.route('/productos', methods=['POST'])
def crear_producto():
    data = request.json
    required_fields = ['nombre', 'descripcion', 'precio', 'disponibilidad']
    
    # Validar que todos los campos necesarios estén en la solicitud
    if all(field in data and data[field] is not None for field in required_fields):
        # Llamar a la función insert_product de test_db.py
        response = test_db.insert_product(data)
        
        # Comprobar si la inserción fue exitosa
        if response.get("status") == "success":
            return jsonify(response), 201
        else:
            return jsonify(response), 500  # Enviar el error si ocurrió un problema al insertar
    else:
        return jsonify({"message": "Por favor complete todos los campos requeridos", "status": "error"}), 400

@app.route('/productos/<int:id_producto>', methods=['PUT']) #
def actualizar_producto(id_producto):
    data = request.json
    required_fields = ['nombre', 'descripcion', 'precio', 'disponibilidad']
    if all(field in data for field in required_fields):
        response = test_db.update_product(id_producto, data)
        if response.get("status") == "success":
            return jsonify(response), 200
        else:
            return jsonify(response), 500
    else:
        return jsonify({"message": "Campos requeridos faltantes", "status": "error"}), 400

@app.route('/productos/<int:id_producto>', methods=['DELETE']) #
def eliminar_producto(nombre):
    response = test_db.delete_product(nombre)
    if response.get("status") == "success":
        return jsonify(response), 200
    else:
        return jsonify(response), 500

@app.route('/productos', methods=['GET']) #
def listar_productos():
    response = test_db.get_all_products()
    return jsonify(response), 200

# @app.route('/promociones', methods=['POST']) 
# def crear_promos():
#     data = request.json
#     required_fields = ['nombre', 'productos_incluidos', 'precio_promocion', 'fecha_inicio', 'fecha_fin']
    
#     # Validar que todos los campos necesarios estén en la solicitud
#     if all(field in data and data[field] is not None for field in required_fields):
#         # Llamar a la función insert_product de test_db.py
#         response = test_db.insert_promo(data)
        
#         # Comprobar si la inserción fue exitosa
#         if response.get("status") == "success":
#             return jsonify(response), 201
#         else:
#             return jsonify(response), 500  # Enviar el error si ocurrió un problema al insertar
#     else:
#         return jsonify({"message": "Por favor complete todos los campos requeridos", "status": "error"}), 400

# @app.route('/promociones/<int:id_promocion>', methods=['PUT']) #
# def actualizar_promo(id_promocion):
#     data = request.json
#     # Validar datos necesarios
#     required_fields = ['nombre', 'productos_incluidos', 'precio_promocion', 'fecha_inicio', 'fecha_fin']
#     if all(field in data and data[field] is not None for field in required_fields):
#         response = test_db.update_promo(id_promocion, data)
#         if response.get("status") == "success":
#             return jsonify(response), 200
#         else:
#             return jsonify(response), 500
#     else:
#         return jsonify({"message": "Campos requeridos faltantes", "status": "error"}), 400

# @app.route('/promociones/<int:id_promocion>', methods=['DELETE']) #
# def eliminar_promo(id_promocion):
#     response = test_db.delete_promo(id_promocion)
#     if response.get("status") == "success":
#         return jsonify(response), 200
#     else:
#         return jsonify(response), 500

@app.route('/pedidos/<int:id_pedido>', methods=['PATCH']) #
def actualizar_estado_pedido(id_pedido):
    data = request.json
    if 'estado' in data:
        response = test_db.update_order_status(id_pedido, data['estado'])
        if response.get("status") == "success":
            return jsonify(response), 200
        else:
            return jsonify(response), 500
    else:
        return jsonify({"message": "Falta el campo 'estado'", "status": "error"}), 400

@app.route('/pedidos/<int:id_pedido>', methods=['DELETE']) #
def eliminar_pedido(id_pedido):
    response = test_db.delete_order(id_pedido)
    if response.get("status") == "success":
        return jsonify(response), 200
    else:
        return jsonify(response), 500


if __name__ == '__main__':
    print('Escuchando en el puerto 5000...')
    app.run(host='0.0.0.0', debug = True)

