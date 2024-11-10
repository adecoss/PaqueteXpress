from flask import Flask, request, jsonify, render_template
import json
import os
from logic.graph_logic import load_graph, calculate_route
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for non-GUI usage
import matplotlib.pyplot as plt

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
        
        # Call calculate_route function
        route_info, total_time, graph_image = calculate_route(
            graph, departamento_origen, provincia_origen, distrito_origen,
            departamento_destino, provincia_destino, distrito_destino, weight
        )

        # Check if route_info or any expected data is missing
        if route_info is None:
            return jsonify({"status": "error", "message": "Error calculating route"}), 500
        
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
        return jsonify({"status": "error", "message": "Error calculating route"}), 500

if __name__ == '__main__':
    app.run(debug=True)

    
    # python app.py
    
    
    