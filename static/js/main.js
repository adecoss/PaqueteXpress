document.addEventListener('DOMContentLoaded', async function () {
    const originDepartment = document.getElementById("origin-department");
    const originProvince = document.getElementById("origin-province");
    const originDistrict = document.getElementById("origin-district");
    const destinationDepartment = document.getElementById("destination-department");
    const destinationProvince = document.getElementById("destination-province");
    const destinationDistrict = document.getElementById("destination-district");
    const routeInfoText = document.getElementById("route-info"); // The textarea for results

    // Fetch peru_location.json data from the server
    let peruLocations;
    try {
        const response = await fetch('/get_locations');
        peruLocations = await response.json();
    } catch (error) {
        console.error("Error fetching location data:", error);
        return;
    }

    // Populate the department dropdowns
    for (let department in peruLocations) {
        originDepartment.innerHTML += `<option value="${department}">${department}</option>`;
        destinationDepartment.innerHTML += `<option value="${department}">${department}</option>`;
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
});