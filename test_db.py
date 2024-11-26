'''
Password: HQhAeTyOLbk9alRd'''


import os
from typing import Any, Dict
from sqlalchemy import QueuePool, create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError


# Configuración de la conexión a la base de datos
DB_URL = "postgresql://postgres.yfpkocqhikzanaovdnha:HQhAeTyOLbk9alRd@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
engine = create_engine(DB_URL, poolclass=QueuePool, pool_size=5, max_overflow=10)
Session = sessionmaker(bind=engine)

def get_schema() -> str:
    # Creación de un nuevo motor de conexión
    engine = create_engine(
        
        "postgresql://postgres.yfpkocqhikzanaovdnha:HQhAeTyOLbk9alRd@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    )
    
    # Uso de inspector para obtener las tablas de la base de datos
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    # Función interna para obtener los detalles de las columnas de una tabla
    def get_column_details(table_name) -> list[str]:
        columns = inspector.get_columns(table_name)
        return [f"{col['name']} ({col['type']})" for col in columns]

    # Recolectar información de las tablas y sus columnas
    schema_info = []
    for table_name in table_names:
        table_info = [f"Table: {table_name}"]
        table_info.append("Columns:")
        table_info.extend(f"  - {column}" for column in get_column_details(table_name))
        schema_info.append("\n".join(table_info))

    # Unir toda la información en un solo string
    return "\n\n".join(schema_info)

async def query(sql_query: str) -> list[dict[str, Any]]:
    print("sql_query: ", sql_query)
    with Session() as session:
        statement = text(sql_query)
        result = session.execute(statement)
        return [dict(row._mapping) for row in result]
# print(get_schema())

# with Session() as session:
#         statement = text('''SELECT nombre,disponibilidad FROM productos WHERE nombre ILIKE '%hamburguesa vegetariana%'; ''')
#         result = session.execute(statement)
#         print([dict(row._mapping) for row in result])

def insert_product(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with Session() as session:
            statement = text("""
                INSERT INTO productos (nombre, descripcion, precio, disponibilidad)
                VALUES (:nombre, :descripcion, :precio, :disponibilidad)
                RETURNING id_producto
            """)
            result = session.execute(statement, data)
            session.commit()
            product_id = result.fetchone()[0]  # Obtener el ID del producto insertado
            return {"message": "Producto creado exitosamente", "product_id": product_id, "status": "success"}
    except SQLAlchemyError as e:
        # Manejo de errores en caso de que ocurra un problema con la base de datos
        return {"message": "Error al crear el producto", "error": str(e), "status": "error"}

# def insert_promo(data: Dict[str, Any]) -> Dict[str, Any]:
#     try:
#         with Session() as session:
#             # Insertar la promoción en la tabla `promociones`
#             promo_statement = text("""
#                 INSERT INTO promociones (nombre, productos_incluidos, precio_promocion, fecha_inicio, fecha_fin)
#                 VALUES (:name, :productos_incluidos, :precio_promocion, :fecha_inicio, :fecha_fin)
#                 RETURNING id_promocion
#             """)
#             promo_result = session.execute(promo_statement, {
#                 'name': data.get('name'),
#                 'productos_incluidos': ','.join(data.get('productos_incluidos', [])),  # Descripción de productos
#                 'precio_promocion': data.get('precio_promocion'),
#                 'fecha_inicio': data.get('fecha_inicio'),
#                 'fecha_fin': data.get('fecha_fin')
#             })
#             id_promocion = promo_result.fetchone()[0]

#             # Obtener los IDs de los productos desde la tabla `productos`
#             productos_incluidos = data.get('productos_incluidos', [])
#             product_ids = []
#             for product_name in productos_incluidos:
#                 product = session.execute(
#                     text("SELECT id_producto FROM productos WHERE nombre = :nombre"),
#                     {'nombre': product_name}
#                 ).fetchone()
#                 if product:
#                     product_ids.append(product[0])
#                 else:
#                     print(f"Producto '{product_name}' no encontrado en la base de datos.")

#             # Insertar los productos relacionados en la tabla `promocion_producto`
#             for product_id in product_ids:
#                 product_statement = text("""
#                     INSERT INTO promocion_producto (id_promocion, id_producto)
#                     VALUES (:id_promocion, :id_producto)
#                 """)
#                 session.execute(product_statement, {
#                     'id_promocion': id_promocion,
#                     'id_producto': product_id
#                 })

#             session.commit()
#             return {"message": "Promoción creada exitosamente", "id_promocion": id_promocion, "status": "success"}

#     except SQLAlchemyError as e:
#         print(f"Error al crear la promoción: {e}")
#         return {"message": "Error al crear la promoción", "error": str(e), "status": "error"}

def update_product(id_producto, data):
    try:
        with Session() as session:
            # Construir dinámicamente los campos a actualizar
            update_fields = []
            for field, value in data.items():
                if value is not None:  # Solo incluir campos no nulos
                    update_fields.append(f"{field} = :{field}")
            
            # Verificar que hay campos válidos para actualizar
            if not update_fields:
                return {"message": "No hay datos para actualizar", "status": "error"}
            
            # Crear la consulta dinámica
            update_statement = text(f"""
                UPDATE productos
                SET {', '.join(update_fields)}
                WHERE id_producto = :id_producto
            """)
            
            # Agregar el ID del producto a los parámetros
            data["id_producto"] = id_producto
            
            # Ejecutar la consulta
            result = session.execute(update_statement, data)
            session.commit()
            
            if result.rowcount > 0:  # Verificar si se actualizó alguna fila
                return {"message": "Producto actualizado exitosamente", "status": "success"}
            else:
                return {"message": "Producto no encontrado", "status": "error"}
    except SQLAlchemyError as e:
        print(f"Error al actualizar el producto: {e}")
        return {"message": "Error al actualizar el producto", "error": str(e), "status": "error"}

def delete_product(nombre):
    try:
        with Session() as session:
            # Consulta para eliminar el producto
            delete_statement = text("""
                DELETE FROM productos WHERE nombre = :nombre
            """)
            
            # Ejecutar la consulta
            result = session.execute(delete_statement, {'nombre': nombre})
            session.commit()
            
            if result.rowcount > 0:  # Verificar si se eliminó alguna fila
                return {"message": "Producto eliminado exitosamente", "status": "success"}
            else:
                return {"message": "Producto no encontrado", "status": "error"}
    except SQLAlchemyError as e:
        print(f"Error al eliminar el producto: {e}")
        return {"message": "Error al eliminar el producto", "error": str(e), "status": "error"}

def get_all_products():
    try:
        with Session() as session:
            statement = text("""
                SELECT id_producto, nombre, descripcion, precio, disponibilidad
                FROM productos
            """)
            result = session.execute(statement).fetchall()

            # Formatear los resultados como una lista de diccionarios
            products = [
                {
                    "id_producto": row[0],
                    "nombre": row[1],
                    "descripcion": row[2],
                    "precio": row[3],
                    "disponibilidad": row[4],
                }
                for row in result
            ]
            return {"message": "Productos obtenidos exitosamente", "products": products, "status": "success"}
    except SQLAlchemyError as e:
        print.error(f"Error al obtener productos: {e}")
        return {"message": "Error al obtener productos", "error": str(e), "status": "error"}

# def update_promo(id_promocion, data):
#     try:
#         with Session() as session:
#             # Actualizar los campos de la promoción
#             promo_statement = text("""
#                 UPDATE promociones
#                 SET nombre = :name, 
#                     productos_incluidos = :productos_incluidos, 
#                     precio_promocion = :precio_promocion, 
#                     fecha_inicio = :fecha_inicio, 
#                     fecha_fin = :fecha_fin
#                 WHERE id_promocion = :id_promocion
#             """)
#             session.execute(promo_statement, {
#                 'id_promocion': id_promocion,
#                 'name': data.get('name'),
#                 'productos_incluidos': ','.join(data.get('productos_incluidos', [])),  # Descripción
#                 'precio_promocion': data.get('precio_promocion'),
#                 'fecha_inicio': data.get('fecha_inicio'),
#                 'fecha_fin': data.get('fecha_fin')
#             })

#             # Actualizar los productos relacionados
#             # Primero eliminar las relaciones antiguas
#             session.execute(
#                 text("DELETE FROM promocion_producto WHERE id_promocion = :id_promocion"),
#                 {'id_promocion': id_promocion}
#             )

#             # Agregar las nuevas relaciones
#             productos_incluidos = data.get('productos_incluidos', [])
#             for product_name in productos_incluidos:
#                 product = session.execute(
#                     text("SELECT id_producto FROM productos WHERE nombre = :nombre"),
#                     {'nombre': product_name}
#                 ).fetchone()
#                 if product:
#                     product_statement = text("""
#                         INSERT INTO promocion_producto (id_promocion, id_producto)
#                         VALUES (:id_promocion, :id_producto)
#                     """)
#                     session.execute(product_statement, {
#                         'id_promocion': id_promocion,
#                         'id_producto': product[0]
#                     })

#             session.commit()
#             return {"message": "Promoción actualizada exitosamente", "status": "success"}
#     except SQLAlchemyError as e:
#         print(f"Error al actualizar la promoción: {e}")
#         return {"message": "Error al actualizar la promoción", "error": str(e), "status": "error"}

# def delete_promo(id_promocion):
#     try:
#         with Session() as session:
#             # Eliminar las relaciones en promocion_producto
#             session.execute(
#                 text("DELETE FROM promocion_producto WHERE id_promocion = :id_promocion"),
#                 {'id_promocion': id_promocion}
#             )

#             # Eliminar la promoción
#             promo_statement = text("DELETE FROM promociones WHERE id_promocion = :id_promocion")
#             result = session.execute(promo_statement, {'id_promocion': id_promocion})
#             session.commit()

#             if result.rowcount > 0:
#                 return {"message": "Promoción eliminada exitosamente", "status": "success"}
#             else:
#                 return {"message": "Promoción no encontrada", "status": "error"}
#     except SQLAlchemyError as e:
#         print(f"Error al eliminar la promoción: {e}")
#         return {"message": "Error al eliminar la promoción", "error": str(e), "status": "error"}

def update_order_status(id_pedido, data):
    try:
        with Session() as session:
            # Validar que el campo `estado` esté en los datos
            if 'estado' not in data or not data['estado']:
                return {"message": "El campo 'estado' es obligatorio", "status": "error"}

            # Actualizar el estado del pedido
            order_statement = text("""
                UPDATE pedidos
                SET estado = :estado
                WHERE id_pedido = :id_pedido
            """)
            result = session.execute(order_statement, {
                'id_pedido': id_pedido,
                'estado': data['estado']
            })
            session.commit()

            if result.rowcount > 0:
                return {"message": "Estado del pedido actualizado exitosamente", "status": "success"}
            else:
                return {"message": "Pedido no encontrado", "status": "error"}
    except SQLAlchemyError as e:
        print(f"Error al actualizar el estado del pedido: {e}")
        return {"message": "Error al actualizar el estado del pedido", "error": str(e), "status": "error"}

def delete_order(id_pedido):
    try:
        with Session() as session:
            # Eliminar primero los detalles del pedido para mantener la integridad referencial
            delete_details_statement = text("""
                DELETE FROM detalle_pedido
                WHERE id_pedido = :id_pedido
            """)
            session.execute(delete_details_statement, {'id_pedido': id_pedido})

            # Eliminar el pedido principal
            delete_order_statement = text("""
                DELETE FROM pedidos
                WHERE id_pedido = :id_pedido
            """)
            result = session.execute(delete_order_statement, {'id_pedido': id_pedido})
            session.commit()
            
            if result.rowcount > 0:  # Verificar si se eliminó alguna fila
                return {"message": "Pedido eliminado exitosamente", "status": "success"}
            else:
                return {"message": "Pedido no encontrado", "status": "error"}
    except SQLAlchemyError as e:
        print(f"Error al eliminar el pedido: {e}")
        return {"message": "Error al eliminar el pedido", "error": str(e), "status": "error"}

def insert_order(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with Session() as session:
            # Verificar si el usuario ya existe en la tabla `usuarios`
            existing_user = session.execute(
                text("SELECT id_usuario FROM usuarios WHERE cedula = :cedula"),
                {'cedula': data.get('cedula')}
            ).fetchone()

            if existing_user:
                user_id = existing_user[0]
            else:
                # Insertar el nuevo usuario con `fecha_registro`
                user_statement = text("""
                    INSERT INTO usuarios (nombre, telefono, direccion, cedula, correo, fecha_registro)
                    VALUES (:name, :phone, :address, :cedula, :email, NOW())
                    RETURNING id_usuario
                """)
                user_result = session.execute(user_statement, {
                    'name': data.get('name'),
                    'phone': data.get('phone'),
                    'address': data.get('address'),
                    'cedula': data.get('cedula'),
                    'email': data.get('email')
                })
                user_id = user_result.fetchone()[0] if user_result else None

            # Aquí deberías calcular el total basado en el precio de cada producto
            total = 0
            for i, product_name in enumerate(data.get('products', [])):
                quantity = data.get('quantity', [])[i]
                
                # Suponiendo que tienes una función para obtener el precio y el id del producto
                product_info = get_product_info_by_name(product_name)
                
                if product_info:
                    price = product_info['price']
                    product_id = product_info['id_producto']
                    total += quantity * price
                else:
                    print(f"Producto '{product_name}' no encontrado en la base de datos.")
                    continue

            # Crear el pedido en la tabla `pedidos`
            order_statement = text("""
                INSERT INTO pedidos (id_usuario, fecha_hora_pedido, total, estado, metodo_entrega, metodo_pago, estado_pago)
                VALUES (:user_id, NOW(), :total, 'pendiente', 'entrega', :payment_method, 'pendiente')
                RETURNING id_pedido
            """)
            order_result = session.execute(order_statement, {
                'user_id': user_id,
                'total': total,
                'payment_method': data.get('payment_method')
            })
            order_id = order_result.fetchone()[0]

            # Insertar detalles del pedido en `detalle_pedido`
            for i, product_name in enumerate(data.get('products', [])):
                quantity = data.get('quantity', [])[i]
                product_info = get_product_info_by_name(product_name)
                
                if product_info:
                    product_id = product_info['id_producto']
                    price = product_info['price']
                    subtotal = quantity * price
                    detail_statement = text("""
                        INSERT INTO detalle_pedido (id_pedido, id_producto, cantidad, precio_unitario, subtotal)
                        VALUES (:order_id, :product_id, :quantity, :unit_price, :subtotal)
                    """)
                    session.execute(detail_statement, {
                        'order_id': order_id,
                        'product_id': product_id,
                        'quantity': quantity,
                        'unit_price': price,
                        'subtotal': subtotal
                    })

            session.commit()
            print({"message": "Orden creada exitosamente", "order_id": order_id, "status": "success"})
            return {"message": "Orden creada exitosamente", "order_id": order_id, "status": "success"}

    except SQLAlchemyError as e:
        print({"message": "Error al crear la orden", "error": str(e), "status": "error"})
        return {"message": "Error al crear la orden", "error": str(e), "status": "error"}

# Ejemplo de función para obtener información del producto
def get_product_info_by_name(product_name: str) -> Dict[str, Any]:
    # Realiza una consulta a la base de datos para obtener el id y el precio
    with Session() as session:
        product = session.execute(
            text("SELECT id_producto, precio FROM productos WHERE nombre = :nombre"),
            {'nombre': product_name}
        ).fetchone()
        if product:
            return {'id_producto': product[0], 'price': product[1]}
        return None

def update_product(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        pass
    except Exception as e:
        e