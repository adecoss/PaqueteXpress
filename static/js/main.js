document.addEventListener('DOMContentLoaded', async function () {
    const originDepartment = document.getElementById("origin-department");
    const originProvince = document.getElementById("origin-province");
    const originDistrict = document.getElementById("origin-district");
    const destinationDepartment = document.getElementById("destination-department");
    const destinationProvince = document.getElementById("destination-province");
    const destinationDistrict = document.getElementById("destination-district");
    const routeInfoText = document.getElementById("route-info"); 

    const originDepartmentFlow = document.getElementById("origin-department-flow");
    const originProvinceFlow = document.getElementById("origin-province-flow");
    const originDistrictFlow = document.getElementById("origin-district-flow");
    const destinationDepartmentFlow = document.getElementById("destination-department-flow");
    const destinationProvinceFlow = document.getElementById("destination-province-flow");
    const destinationDistrictFlow = document.getElementById("destination-district-flow");

    // peru_location.json
    let peruLocations;
    try {
        const response = await fetch('/get_locations');
        peruLocations = await response.json();
    } catch (error) {
        console.error("Error fetching location data:", error);
        return;
    }

   // Llenar dropdowns para ambos formularios
   for (let department in peruLocations) {
    originDepartment.innerHTML += `<option value="${department}">${department}</option>`;
    destinationDepartment.innerHTML += `<option value="${department}">${department}</option>`;

    originDepartmentFlow.innerHTML += `<option value="${department}">${department}</option>`;
    destinationDepartmentFlow.innerHTML += `<option value="${department}">${department}</option>`;
    }

    const updateProvinces = (department, selectElement) => {
        const provinces = peruLocations[department] || {};
        selectElement.innerHTML = '<option value="">Seleccionar</option>'; // Clear previous options
        for (let province in provinces) {
            selectElement.innerHTML += `<option value="${province}">${province}</option>`;
        }
        selectElement.disabled = !Object.keys(provinces).length;
    };

    const updateDistricts = (department, province, selectElement) => {
        const districts = peruLocations[department]?.[province] || [];
        selectElement.innerHTML = '<option value="">Seleccionar</option>'; // Clear previous options
        districts.forEach(district => {
            selectElement.innerHTML += `<option value="${district}">${district}</option>`;
        });
        selectElement.disabled = !districts.length;
    };

    // Eventos para formulario de Flujo
    originDepartmentFlow.addEventListener('change', function () {
        updateProvinces(this.value, originProvinceFlow);
        originDistrictFlow.disabled = true;
    });

    originProvinceFlow.addEventListener('change', function () {
        updateDistricts(originDepartmentFlow.value, this.value, originDistrictFlow);
    });

    destinationDepartmentFlow.addEventListener('change', function () {
        updateProvinces(this.value, destinationProvinceFlow);
        destinationDistrictFlow.disabled = true;
    });

    destinationProvinceFlow.addEventListener('change', function () {
        updateDistricts(destinationDepartmentFlow.value, this.value, destinationDistrictFlow);
    });
    
    // Eventos para formulario de Rutas
    originDepartment.addEventListener('change', function () {
        updateProvinces(this.value, originProvince);
        originDistrict.disabled = true;
    });

    originProvince.addEventListener('change', function () {
        updateDistricts(originDepartment.value, this.value, originDistrict);
    });

    destinationDepartment.addEventListener('change', function () {
        updateProvinces(this.value, destinationProvince);
        destinationDistrict.disabled = true;
    });

    destinationProvince.addEventListener('change', function () {
        updateDistricts(destinationDepartment.value, this.value, destinationDistrict);
    });

    document.getElementById("show-route").addEventListener("click", function () {
        document.getElementById("route-form").style.display = "block";
        document.getElementById("flow-form").style.display = "none";
    });

    document.getElementById("show-flow").addEventListener("click", function () {
        document.getElementById("route-form").style.display = "none";
        document.getElementById("flow-form").style.display = "block";
    });

    document.getElementById("route-form").onsubmit = async function(e) {
        e.preventDefault();
    
        // Gather form data
        const departamentoOrigen = document.getElementById("origin-department").value;
        const provinciaOrigen = document.getElementById("origin-province").value;
        const distritoOrigen = document.getElementById("origin-district").value;

        const departamentoDestino = document.getElementById("destination-department").value;
        const provinciaDestino = document.getElementById("destination-province").value;
        const distritoDestino = document.getElementById("destination-district").value;
        
        const weight = parseInt(document.getElementById("package-weight").value, 10);
        const submitButton = document.querySelector("button[type='submit']");

        // Update the text area with the waiting message
        console.log('Updating route info...');
        routeInfoText.value = 'Esperando resultados...';

        // Create data payload
        const payload = {
            departamento_origen: departamentoOrigen,
            provincia_origen: provinciaOrigen,
            distrito_origen: distritoOrigen,
            departamento_destino: departamentoDestino,
            provincia_destino: provinciaDestino,
            distrito_destino: distritoDestino,
            weight: weight
        };
    
        try {
            const response = await fetch("/calculate_route", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });
    
            const result = await response.json();
            if (result.status === "success") {
                // Handle successful route calculation
                displayRouteInfo(result.route_info, result.total_time, result.graph_image);
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Error calculating the route");
        }
    };

    function displayRouteInfo(routeInfo, totalTime, graphImage) {
        const routeInfoText = document.getElementById("route-info");
        routeInfoText.value = ''; // Clear previous content

        // Display each route segment in the textarea
        routeInfo.segments.forEach(segment => {
            routeInfoText.value += `\nDesde: ${segment.from}\nHacia: ${segment.to}\nDistancia: ${segment.distance} km\nTiempo: ${segment.time}\n\n`;
        });

        // Display total distance and time
        routeInfoText.value += `Distancia Total: ${routeInfo.total_distance} km\nTiempo Total: ${totalTime}\n`;

        // Display the graph image
        const graphImg = document.getElementById('graph-image');
        graphImg.src = `data:image/png;base64,${graphImage}`;
        graphImg.style.display = 'block'; // Ensure the image is displayed
    }

    document.getElementById("flow-form").onsubmit = async function(e) {
        e.preventDefault();
    
        const departamentoOrigen = document.getElementById("origin-department-flow").value;
        const provinciaOrigen = document.getElementById("origin-province-flow").value;
        const distritoOrigen = document.getElementById("origin-district-flow").value;
    
        const departamentoDestino = document.getElementById("destination-department-flow").value;
        const provinciaDestino = document.getElementById("destination-province-flow").value;
        const distritoDestino = document.getElementById("destination-district-flow").value;
        
        const packageQuantity = parseInt(document.getElementById("package-quantity").value, 10);
    
        const payload = {
            departamento_origen: departamentoOrigen,
            provincia_origen: provinciaOrigen,
            distrito_origen: distritoOrigen,
            departamento_destino: departamentoDestino,
            provincia_destino: provinciaDestino,
            distrito_destino: distritoDestino,
            package_quantity: packageQuantity
        };
    
        try {
            const response = await fetch("/calculate_flow", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            if (result.status === "success") {
                displayFlowInfo(result.flow_info, result.total_flow, result.graph_image);
            } else {
                alert(result.message);
            }
        } catch (error) {
            console.error("Error:", error);
            alert("Error calculating the flow");
        }
    };

    function displayFlowInfo(flowInfo, totalFlow, graphImage) {
        const routeInfoText = document.getElementById("route-info");
        routeInfoText.value = ''; // Limpiar contenido previo
        
        flowInfo.segments.forEach(segment => {
            // Crear la cadena de texto con la ruta completa
            const fullRoute = segment.path.join(' -> ');  // Unir los nodos con ' -> '
            
            routeInfoText.value += `Ruta: ${fullRoute}\nFlujo: ${segment.flow} paquetes\n\n`;
        });
        
        routeInfoText.value += `Flujo Total: ${totalFlow} paquetes\n`;
    
        // Mostrar la imagen del grafo
        const graphImg = document.getElementById('graph-image');
        graphImg.src = `data:image/png;base64,${graphImage}`;
        graphImg.style.display = 'block';
    }

});