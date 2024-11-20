from flask import jsonify
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')  # Use Agg backend for non-GUI usage
import heapq,base64
from itertools import islice
from io import BytesIO

# Cargar el GraphML
def load_graph(filepath):
    try:
        G = nx.read_graphml(filepath)
        return G
    except Exception as e:
        raise ValueError(f"Error loading the GraphML file: {e}")

# Dijkstra' para encontrar camino mas corto
def dijkstra(graph, start, end):
    distances = {node: float('inf') for node in graph.nodes}
    previous_nodes = {node: None for node in graph.nodes}
    distances[start] = 0
    priority_queue = [(0, start)]

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_node == end:
            break

        for neighbor in graph.neighbors(current_node):
            weight = float(graph[current_node][neighbor].get('weight', 1))
            new_distance = current_distance + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                previous_nodes[neighbor] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbor))

    path = []
    current_node = end
    while current_node is not None:
        path.append(current_node)
        current_node = previous_nodes[current_node]
    path.reverse()

    return path, distances[end]

# Calcular la ruta (usando el dijstra implementado)
def calculate_route(graph, departamento_origen, provincia_origen, distrito_origen,
                    departamento_destino, provincia_destino, distrito_destino, weight):
    try:
        origin = f"{distrito_origen.upper()} ({provincia_origen.upper()}, {departamento_origen.upper()})"
        destination = f"{distrito_destino.upper()} ({provincia_destino.upper()}, {departamento_destino.upper()})"
        
        if origin not in graph.nodes or destination not in graph.nodes:
            raise ValueError("Nodo Origen o Destino no encontrado en el grafo.")
        
        path, total_distance = dijkstra(graph, origin, destination)
        
        #Datos del Dron
        max_speed = 80
        min_speed = 50
        speed = max(min_speed, max_speed - 2 * weight)
        total_time_hours = total_distance / speed
        total_time_minutes = int(total_time_hours * 60)
        
        #Segmentos del camono total
        route_segments = []
        for i in range(len(path) - 1):
            start = path[i]
            end = path[i + 1]
            segment_distance = graph.edges[start, end].get('weight', 1)
            segment_time_hours = segment_distance / speed
            segment_time_minutes = int(segment_time_hours * 60)
            
            route_segments.append({
                'from': start,
                'to': end,
                'distance': round(segment_distance, 2),
                'time': f"{segment_time_minutes // 60} hours {segment_time_minutes % 60} minutes"
            })
        
        route_info = {
            'segments': route_segments,
            'total_distance': round(total_distance, 2),
            'total_time': f"{total_time_minutes // 60} hours {total_time_minutes % 60} minutes"
        }

        graph_image = visualize_route(graph, path, total_distance)
        if not graph_image:  # Ensure that the graph image is successfully encoded
            return jsonify({"status": "error", "message": "Error generating graph image"}), 500
        return route_info, route_info['total_time'], graph_image

    except ValueError as ve:
        print(ve)
        return None, None, None
    except Exception as e:
        print("Error in calculate_route:", e)
        return None, None, None

# Visualisacion de la route en un grafo
def visualize_route(graph, route, total_distance):
    """Visualize the route on the graph and return as a base64-encoded image."""
    route_edges = [(route[i], route[i + 1]) for i in range(len(route) - 1)]
    route_subgraph = graph.edge_subgraph(route_edges)
    all_nodes_in_route = list(set(route))
    subgraph_route = graph.subgraph(all_nodes_in_route)

    plt.figure(figsize=(16, 16))
    pos = nx.spring_layout(subgraph_route, k=0.3, iterations=50, seed=42)
    node_size = 300

    nx.draw(subgraph_route, pos, with_labels=True, node_size=node_size, node_color='lightblue',
            edge_color='gray', width=1.5, alpha=0.7)
    nx.draw_networkx_edges(route_subgraph, pos, edge_color='red', width=2)
    nx.draw_networkx_nodes(route_subgraph, pos, nodelist=[route[0], route[-1]], node_color='red', node_size=500)
    plt.title(f'Route from {route[0]} to {route[-1]} (Total Distance: {round(total_distance, 2)} km)')

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    base64_image = base64.b64encode(img_buffer.read()).decode('utf-8')
    plt.close()

    return base64_image

    
def ford_fulkerson(graph, source, sink, package_capacity):
    # Crear un grafo residual basado en el grafo original
    residual_graph = nx.DiGraph()
    for u, v, data in graph.edges(data=True):
        # Asegura que cada arista tiene una capacidad que no supere `package_capacity`
        residual_graph.add_edge(u, v, capacity=min(data.get('capacity', float('inf')), package_capacity))
        residual_graph.add_edge(v, u, capacity=0)  # Inicialmente, no hay flujo en la dirección inversa
        print(f"Residual Edge: {u} -> {v}, Capacity: {data['capacity']}")
    
    # Inicializar el flujo máximo
    max_flow = 0
    flow_segments = []
    
    # Algoritmo principal de Ford-Fulkerson con búsqueda de caminos aumentantes
    while True:
        # Buscar un camino aumentante usando búsqueda en anchura (BFS)
        parent_map = {}
        visited = set([source])
        queue = [(source, float('inf'))]

        found_path = False
        while queue:
            current_node, flow = queue.pop(0)

            # Verificar cada vecino del nodo actual
            for neighbor in residual_graph.neighbors(current_node):
                if neighbor not in visited and residual_graph[current_node][neighbor]['capacity'] > 0:
                    # Calcular el flujo del camino aumentante mínimo
                    new_flow = min(flow, residual_graph[current_node][neighbor]['capacity'])
                    parent_map[neighbor] = current_node

                    # Si llegamos al nodo sink, encontramos un camino aumentante
                    if neighbor == sink:
                        max_flow += new_flow
                        path = []
                        current = sink
                        
                        # Retrocede por el camino para ajustar capacidades
                        while current != source:
                            previous = parent_map[current]
                            residual_graph[previous][current]['capacity'] -= new_flow
                            residual_graph[current][previous]['capacity'] += new_flow
                            # Añadir el segmento como una tupla
                            flow_segments.append((previous, current, new_flow))
                            current = previous

                        # Guardar el segmento de flujo en flow_segments 
                        found_path = True
                        break

                    # Añadir al vecino a la cola de exploración y marcarlo como visitado
                    queue.append((neighbor, new_flow))
                    visited.add(neighbor)
            
            if found_path:
                break

        # Si no encontramos un camino aumentante, terminamos
        if not found_path:
            break

    return max_flow, flow_segments

def calculate_flow(graph, departamento_origen, provincia_origen, distrito_origen,
                   departamento_destino, provincia_destino, distrito_destino, package_quantity):
    # Encuentra el nodo origen y destino en el grafo
    nodo_origen = f"{departamento_origen}-{provincia_origen}-{distrito_origen}"
    nodo_destino = f"{departamento_destino}-{provincia_destino}-{distrito_destino}"

    # Obtener las tres rutas más cortas entre origen y destino
    try:
        rutas_alternativas = list(
            nx.shortest_simple_paths(graph, nodo_origen, nodo_destino, weight='distance')
        )[:3]
    except nx.NetworkXNoPath:
        return None, 0, None  # No existe una ruta entre los nodos

    # Calcular la capacidad máxima de flujo para cada ruta basada en el área
    flujo_rutas = []
    flujo_total = 0
    paquetes_restantes = package_quantity

    for i, ruta in enumerate(rutas_alternativas):
        flujo_ruta = []
        flujo_ruta_total = 0

        for j in range(len(ruta) - 1):
            nodo_actual = ruta[j]
            nodo_siguiente = ruta[j + 1]

            # Obtiene la capacidad del nodo actual
            capacidad_nodo = graph.nodes[nodo_actual].get('area', 0) * 5
            paquetes_enviar = min(capacidad_nodo, paquetes_restantes)

            # Reduce la cantidad de paquetes restantes y agrega los detalles de flujo
            paquetes_restantes -= paquetes_enviar
            flujo_ruta.append({
                "desde": nodo_actual,
                "hacia": nodo_siguiente,
                "paquetes": paquetes_enviar
            })
            flujo_ruta_total += paquetes_enviar

            # Detener si ya no quedan paquetes por enviar
            if paquetes_restantes <= 0:
                break

        flujo_rutas.append({
            "ruta_id": i + 1,
            "detalles": flujo_ruta,
            "total_recibidos": flujo_ruta_total
        })
        flujo_total += flujo_ruta_total

        # Salimos del bucle si todos los paquetes han sido enviados
        if paquetes_restantes <= 0:
            break

    # Generar imagen del grafo con las rutas utilizadas
    fig, ax = plt.subplots(figsize=(10, 10))
    pos = nx.spring_layout(graph)
    nx.draw(graph, pos, ax=ax, with_labels=True, node_size=50, font_size=8)
    
    # Dibujar cada ruta
    for ruta in rutas_alternativas:
        edges = [(ruta[i], ruta[i + 1]) for i in range(len(ruta) - 1)]
        nx.draw_networkx_edges(graph, pos, edgelist=edges, ax=ax, edge_color="r", width=2)

    # Convertir gráfico a imagen Base64 para enviar a Flask
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    graph_image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)

    return flujo_rutas, flujo_total, paquetes_restantes, graph_image_base64

def visualize_flow(graph, flow_segments, max_flow):
    if not flow_segments:
        print("No hay segmentos de flujo para visualizar.")
        return None
    
    try:
        # Crear un subgrafo con los nodos y aristas involucrados en el flujo
        edges_used = [(u, v) for u, v, flow in flow_segments]
        subgraph = graph.edge_subgraph(edges_used)
        involved_nodes = set([node for edge in edges_used for node in edge])
        subgraph_nodes = graph.subgraph(involved_nodes)

        # Generar posiciones para los nodos
        pos = nx.spring_layout(subgraph_nodes, k=0.5, iterations=50, seed=42)

        # Configurar visualización
        plt.figure(figsize=(16, 16))
        nx.draw(subgraph_nodes, pos, with_labels=True, node_size=300, node_color='lightblue', edge_color='gray')
        nx.draw_networkx_edges(graph, pos, edgelist=edges_used, edge_color='red', width=2)

        # Añadir etiquetas de flujo a las aristas
        edge_labels = {(u, v): f"{flow}" for u, v, flow in flow_segments}
        nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=10)

        # Título del grafo con el flujo total
        plt.title(f"Flujo máximo: {max_flow} drones", fontsize=14)

        # Convertir la figura a base64
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        base64_image = base64.b64encode(img_buffer.read()).decode('utf-8')
        plt.close()

        return base64_image
    except Exception as e:
        print("Error en visualize_flow:", e)
        return None
   




























































def calculate_routes_and_flow(graph, origin, destination, package_quantity):
    
    # Obtener las primeras 250 rutas más cortas
    all_paths = list(islice(nx.shortest_simple_paths(graph, source=origin, target=destination, weight='weight'), 250))
    
    # Seleccionar rutas únicas con mínima superposición
    selected_routes = []
    max_common_nodes = 1  # Permitimos máximo 1 nodo común (excepto origen y destino)

    for path in all_paths:
        if len(selected_routes) == 3:  # Limitar a 3 rutas
            break
        
        # Verificar superposición con rutas ya seleccionadas
        is_unique = True
        for selected_path in selected_routes:
            common_nodes = set(path[1:-1]) & set(selected_path[1:-1])  # Comparar nodos intermedios
            if len(common_nodes) > max_common_nodes:  # Demasiados nodos comunes
                is_unique = False
                break
        
        if is_unique or len(selected_routes) == 0:  # Si es única o es la primera ruta
            selected_routes.append(path)

    # Parámetros para el flujo
    route_capacity = 2000
    remaining_packages = package_quantity
    total_flow = 0
    segments = []

    # Asignar paquetes a las rutas seleccionadas
    for idx, path in enumerate(selected_routes):
        if remaining_packages <= 0:
            break
        
        # Cantidad de paquetes asignada a esta ruta
        flow = min(route_capacity, remaining_packages)
        total_flow += flow
        remaining_packages -= flow

        # Añadir el segmento con los detalles
        segments.append({
            "from": path[0],
            "to": path[-1],
            "flow": flow,
            "path": path  # Ruta completa
        })

    # Mensaje de resultado
    result_message = (
        f"El flujo máximo alcanzado fue de {total_flow}. "
        f"{remaining_packages} paquetes deberán esperar." if remaining_packages > 0
        else f"El flujo total de {package_quantity} paquetes fue asignado exitosamente."
    )

    return segments, total_flow, remaining_packages, result_message



def generate_graph_image(graph, routes, origin=None, destination=None):

   # Configurar la posición de los nodos solo para los nodos relevantes
    relevant_nodes = set([node for route in routes for node in route])
    subgraph = graph.subgraph(relevant_nodes)
    pos = nx.spring_layout(subgraph)  # Calcular posiciones solo para el subgrafo

    plt.figure(figsize=(15, 15))

    # Dibujar las rutas relevantes en el grafo
    for route in routes:
        edges = [(route[i], route[i + 1]) for i in range(len(route) - 1)]
        nx.draw_networkx_edges(subgraph, pos, edgelist=edges, edge_color="red", width=2)

    # Asignar colores a los nodos (origen y destino en rojo, otros en azul)
    node_colors = []
    for node in subgraph.nodes():
        if node == origin:
            node_colors.append("red")
        elif node == destination:
            node_colors.append("red")
        else:
            node_colors.append("skyblue")

    # Dibujar nodos y etiquetas
    nx.draw_networkx_nodes(subgraph, pos, node_size=500, node_color=node_colors)
    nx.draw_networkx_labels(subgraph, pos, font_size=8)

    # Añadir título a la imagen
    plt.title("Grafo de Flujo", fontsize=16)

    # Guardar la imagen como PNG en memoria
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded_image = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return encoded_image
