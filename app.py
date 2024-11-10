from flask import Flask, request, jsonify, render_template
from matplotlib import pyplot as plt
from logic.graph_logic import load_graph, calculate_route, visualize_route
import json
import os
import base64
from io import BytesIO

app = Flask(__name__)

# Load the graph data once
graph = load_graph('logic/grafo_distritos_peru.graphml')

# Load peru_location.json once
def load_peru_location():
    with open(os.path.join('logic', 'peru_location.json'), encoding='utf-8') as f:
        return json.load(f)

peru_locations = load_peru_location()

def visualize_route(graph, route):
    # Create the plot as before...
    plt.figure(figsize=(8, 8))
    # (rest of the plotting code)
    plt.title(f'Route from {route[0]} to {route[-1]}')
    
    # Save plot to a BytesIO object instead of displaying it in a popup
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    base64_image = base64.b64encode(img_buffer.read()).decode('utf-8')
    plt.close()

    return base64_image

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
        
        # Extract and normalize the inputs
        departamento_origen = data.get('departamento_origen', '').strip()
        provincia_origen = data.get('provincia_origen', '').strip()
        distrito_origen = data.get('distrito_origen', '').strip()
        
        departamento_destino = data.get('departamento_destino', '').strip()
        provincia_destino = data.get('provincia_destino', '').strip()
        distrito_destino = data.get('distrito_destino', '').strip()
        
        weight = int(data.get('weight', 0))
        if weight > 15:
            return jsonify({"status": "error", "message": "El peso no puede exceder los 15 kg"}), 400
        
        # Log origin and destination for debugging
        print(f"Received origin: {departamento_origen}, {provincia_origen}, {distrito_origen}")
        print(f"Received destination: {departamento_destino}, {provincia_destino}, {distrito_destino}")
        
        # Call the route calculation function with the fully qualified names
        route_info, total_time, graph_image = calculate_route(
            graph, departamento_origen, provincia_origen, distrito_origen,
            departamento_destino, provincia_destino, distrito_destino, weight
        )

        if route_info is None:
            return jsonify({"status": "error", "message": "Error calculating route"}), 500

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
    
    
    