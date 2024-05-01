#Para conectar un cliente Python a una máquina de estados finita (FSM) a través de OPC UA, primero debes tener claro cómo está implementada la FSM y qué tipo de datos deseas intercambiar entre el cliente y la máquina de estados.

#A continuación, te proporciono un ejemplo básico de cómo podrías conectar un cliente Python a una FSM a través de OPC UA:

#Supongamos que la FSM está representada por un servidor OPC UA que tiene un nodo para el estado actual y otro nodo para recibir comandos de transición de estado.

from opcua import Client

# Dirección del servidor OPC UA
url = "opc.tcp://localhost:4840"

# Crear un cliente OPC UA
client = Client(url)

try:
    # Conectar al servidor OPC UA
    client.connect()

    # Obtener el nodo raíz del servidor
    root_node = client.get_root_node()

    # Recorrer los nodos hijos del nodo raíz
    print("Contenido del servidor OPC UA:")
    for node in root_node.get_children():
        print(node)
        
        for node_2 in node.get_children():
            print(node_2)

finally:
    # Desconectar del servidor OPC UA
    client.disconnect()

#Este es solo un ejemplo básico y genérico. Debes ajustarlo según cómo esté implementada tu FSM y cómo se hayan configurado los nodos en el servidor OPC UA. Asegúrate de reemplazar las direcciones de los nodos y cualquier otro detalle específico de tu configuración.