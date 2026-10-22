
function Visualization() {

    // Geographic boundaries of the Netherlands
    var netherlandsBounds = L.latLngBounds(
        [50.7, 3.2],
        [53.7, 7.3]
    );

    // Initialize Leaflet map
    var map = L.map("geo-map", {
        maxBounds: netherlandsBounds.pad(0.1),
        maxBoundsViscosity: 1.0
    });

    map.fitBounds(netherlandsBounds, {
        padding: [20, 20]
    });

    map.setMinZoom(map.getZoom());

    // OpenStreetMap background
    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            attribution: "&copy; OpenStreetMap contributors",
            maxZoom: 19
        }
    ).addTo(map);

    // Status colors
    var colors = {
        "Active": "green",
        "Planned": "orange",
        "Currently Installing": "#0d6efd",
        "Not Available": "red",
        "Unknown": "gray"
    };

    // Convert raw fiber statuses into dashboard categories
    function getCategory(status) {

        if (status === "Active") return "Active";
        if (status === "Planned") return "Planned";
        if (status === "Currently Installing") return "Currently Installing";
        if (status === "Not Available") return "Not Available";

        return "Unknown";
    }

    // Marker layer
    var markers = L.layerGroup().addTo(map);

    // Store loaded addresses
    var currentData = [];

    // Filter elements
    var statusFilter = document.getElementById("status-filter");
    var cityFilter = document.getElementById("city-filter");


    // Populate city filter from CSV data
    function populateCities(data) {

        // Get unique, nonempty city names
        var cities = [...new Set(
            data.map(function(d) {
                return (d.city || "").trim();
            }).filter(function(city) {
                return city !== "";
            })
        )].sort(function(a, b) {
            return a.localeCompare(b);
        });

        // Reset dropdown
        cityFilter.innerHTML = "";

        var allOption = document.createElement("option");
        allOption.value = "All";
        allOption.textContent = "All Cities";
        cityFilter.appendChild(allOption);

        // Add one option per city
        cities.forEach(function(city) {

            var option = document.createElement("option");

            option.value = city;
            option.textContent = city;

            cityFilter.appendChild(option);
        });
    }



    // Update statistics and distribution
    function displayData(data) {

        currentData = data;

        var total = data.length;

        var counts = {
            "Active": 0,
            "Planned": 0,
            "Currently Installing": 0,
            "Not Available": 0,
            "Unknown": 0
        };

        data.forEach(function(d) {
            counts[getCategory(d.fiber_status)]++;
        });

        // Statistics
        document.getElementById("total-count").textContent = total;
        document.getElementById("active-count").textContent =
            counts["Active"];
        document.getElementById("planned-count").textContent =
            counts["Planned"];
        document.getElementById("currently-installing-count").textContent =
            counts["Currently Installing"];
        document.getElementById("not-available-count").textContent =
            counts["Not Available"];
        document.getElementById("unknown-count").textContent =
            counts["Unknown"];

        // Distribution bar
        document.getElementById("active-bar").style.width =
            (total ? counts["Active"] / total * 100 : 0) + "%";

        document.getElementById("planned-bar").style.width =
            (total ? counts["Planned"] / total * 100 : 0) + "%";

        document.getElementById("currently-installing-bar").style.width =
            (total ? counts["Currently Installing"] / total * 100 : 0) + "%";

        document.getElementById("not-available-bar").style.width =
            (total ? counts["Not Available"] / total * 100 : 0) + "%";

        document.getElementById("unknown-bar").style.width =
            (total ? counts["Unknown"] / total * 100 : 0) + "%";

        // Populate city dropdown
        populateCities(data);

        // Display all addresses initially
        updateMap();

        console.log("Total addresses:", total);
        console.log("Status distribution:", counts);
    }



    // Display filtered addresses

    function updateMap() {

        markers.clearLayers();

        var selectedStatus = statusFilter.value;
        var selectedCity = cityFilter.value;

        var count = 0;
        var bounds = [];

        currentData.forEach(function(d) {

            var category = getCategory(d.fiber_status);

            // Filter by status
            if (
                selectedStatus !== "All" &&
                category !== selectedStatus
            ) {
                return;
            }

            // Filter by city
            if (
                selectedCity !== "All" &&
                (d.city || "").trim() !== selectedCity
            ) {
                return;
            }

            // Check missing coordinates
            if (
                d.latitude == null ||
                d.longitude == null ||
                d.latitude === "" ||
                d.longitude === ""
            ) {
                return;
            }

            var lat = Number(d.latitude);
            var lon = Number(d.longitude);

            // Validate coordinates
            if (
                !Number.isFinite(lat) ||
                !Number.isFinite(lon)
            ) {
                return;
            }

            // Scale the map
            if (!netherlandsBounds.contains([lat, lon])) {
                return;
            }

            // Create marker
            var marker = L.circleMarker([lat, lon], {
                radius: 7,
                color: "white",
                weight: 1,
                fillColor: colors[category],
                fillOpacity: 0.85
            });

            // Popup
            var popup = document.createElement("div");

            var addressLine = document.createElement("strong");
            addressLine.textContent =
                (d.street || "") + " " +
                (d.house_number || "") +
                (d.addition ? "-" + d.addition : "");

            var locationLine = document.createElement("div");
            locationLine.textContent =
                (d.postcode || "") + " " + (d.city || "");

            var statusLine = document.createElement("div");
            statusLine.textContent =
                "Fiber Status: " + (d.fiber_status || "Unknown");

            popup.appendChild(addressLine);
            popup.appendChild(locationLine);
            popup.appendChild(statusLine);

            marker.bindPopup(popup);
            markers.addLayer(marker);

            bounds.push([lat, lon]);
            count++;
        });


        // Zoom to selected city when filtering
        if (selectedCity !== "All" && bounds.length > 0) {

            map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 13
            });

        } else if (selectedCity === "All") {

            // Return to Netherlands view
            map.fitBounds(netherlandsBounds, {
                padding: [20, 20]
            });
        }
    }


  
    // Load JSON data from Flask
    fetch("/api/fiber-status")

        .then(function(response) {

            if (!response.ok) {
                throw new Error("Cannot retrieve fiber status data");
            }

            return response.json();
        })

        .then(function(data) {

            if (!Array.isArray(data)) {
                throw new Error("Invalid API response");
            }

            displayData(data);
        })

        .catch(function(error) {
            console.error("Error loading data:", error);
        });



    statusFilter.addEventListener("change", updateMap);
    cityFilter.addEventListener("change", updateMap);
}
