from flask import jsonify
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')  # Use Agg backend for non-GUI usage
import heapq,base64
from io import BytesIO

# Load GraphML file
def load_graph(filepath):
    """Load a GraphML file into a NetworkX graph."""
    try:
        G = nx.read_graphml(filepath)
        return G
    except Exception as e:
        raise ValueError(f"Error loading the GraphML file: {e}")

# Dijkstra's algorithm to find the shortest path
def dijkstra(graph, start, end):
    """Implement Dijkstra's algorithm to find the shortest path in the graph."""
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

# Calculate the route between two points
def calculate_route(graph, departamento_origen, provincia_origen, distrito_origen,
                    departamento_destino, provincia_destino, distrito_destino, weight):
    try:
        origin = f"{distrito_origen.upper()} ({provincia_origen.upper()}, {departamento_origen.upper()})"
        destination = f"{distrito_destino.upper()} ({provincia_destino.upper()}, {departamento_destino.upper()})"
        
        if origin not in graph.nodes or destination not in graph.nodes:
            raise ValueError("Origin or destination node not found in the graph.")
        
        path, total_distance = dijkstra(graph, origin, destination)
        
        max_speed = 80
        min_speed = 50
        speed = max(min_speed, max_speed - 2 * weight)
        total_time_hours = total_distance / speed
        total_time_minutes = int(total_time_hours * 60)
        
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

# Visualization of the route in the graph
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
