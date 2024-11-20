from flask import Flask, request, jsonify, render_template
from logic.graph_logic import calculate_routes_and_flow, generate_graph_image, load_graph, calculate_route, calculate_flow
import json, os, matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')  # Use Agg backend for non-GUI usage

app = Flask(__name__)

graph = load_graph('logic/grafo_distritos_peru.graphml')

def load_peru_location():
    with open(os.path.join('logic', 'peru_location.json'), encoding='utf-8') as f:
        return json.load(f)

peru_locations = load_peru_location()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_locations', methods=['GET'])
def get_locations():
    return jsonify(peru_locations)

@app.route('/calculate_route', methods=['POST'])
def calculate_route_api():
    try:
        data = request.get_json()
        departamento_origen = data.get('departamento_origen', '').strip()
        provincia_origen = data.get('provincia_origen', '').strip()
        distrito_origen = data.get('distrito_origen', '').strip()
        departamento_destino = data.get('departamento_destino', '').strip()
        provincia_destino = data.get('provincia_destino', '').strip()
        distrito_destino = data.get('distrito_destino', '').strip()
        weight = int(data.get('weight', 0))
        
        if weight > 15:
            return jsonify({"status": "error", "message": "El peso no puede exceder los 15 kg"}), 400
        print("HERE")
        # Call calculate_route function
        route_info, total_time, graph_image = calculate_route(
            graph, departamento_origen, provincia_origen, distrito_origen,
            departamento_destino, provincia_destino, distrito_destino, weight
        )
        
        # Check if route_info or any expected data is missing
        if route_info is None:
            return jsonify({"status": "error", "message": "Error Calculando La Ruta"}), 500
        
        # Log route details to verify correctness
        print("Route Info:", route_info)
        print("Total Time:", total_time)
        print("Graph Image (truncated):", graph_image[:100])  # Print a snippet of the image to verify
        
        # Return the response in expected structure
        return jsonify({
            "status": "success",
            "route_info": route_info,
            "total_time": total_time,
            "graph_image": graph_image
        })
    except Exception as e:
        print("Error in calculate_route_api:", e)
        return jsonify({"status": "error", "message": "Error Calculando La Ruta"}), 500


@app.route('/calculate_flow', methods=['POST'])
def calculate_flow_api():
    try:
        data = request.get_json()

        # Extraer y limpiar los datos de entrada
        departamento_origen = data.get('departamento_origen', '').strip().upper()
        provincia_origen = data.get('provincia_origen', '').strip().upper()
        distrito_origen = data.get('distrito_origen', '').strip().upper()

        departamento_destino = data.get('departamento_destino', '').strip().upper()
        provincia_destino = data.get('provincia_destino', '').strip().upper()
        distrito_destino = data.get('distrito_destino', '').strip().upper()

        package_quantity = int(data.get('package_quantity', 0))

        # Generar nombres de nodos en el formato correcto
        origin = f"{distrito_origen} ({provincia_origen}, {departamento_origen})"
        destination = f"{distrito_destino} ({provincia_destino}, {departamento_destino})"

        # Validar la cantidad de paquetes
        if package_quantity > 6000:
            return jsonify({"status": "error", "message": "La cantidad de paquetes no puede exceder los 6000"}), 400

        # Validar la existencia de los nodos en el grafo
        if origin not in graph.nodes or destination not in graph.nodes:
            return jsonify({"status": "error", "message": "El origen o destino no existen en el grafo"}), 400

        # Calcular el flujo y las rutas
        flow_segments, total_flow, remaining_packages, result_message = calculate_routes_and_flow(
            graph, origin, destination, package_quantity
        )

        # Reconstruir los paths si no están definidos
        for segment in flow_segments:
            if "path" not in segment:
                segment["path"] = [segment["from"], segment["to"]]
            
        # Generar la visualización del grafo con las rutas
        graph_image = generate_graph_image(graph, [segment["path"] for segment in flow_segments],origin,destination)
       
        # Devolver la respuesta
        return jsonify({
            "status": "success",
            "flow_info": {"segments": flow_segments},
            "total_flow": total_flow,
            "remaining_packages": remaining_packages,
            "message": result_message,
            "graph_image": graph_image
        })

    except Exception as e:
        print("Error en calculate_flow_api:", e)
        return jsonify({"status": "error", "message": "Error calculando el flujo"}), 500


if __name__ == '__main__':
    app.run(debug=True)

    # python app.py
    
    
    