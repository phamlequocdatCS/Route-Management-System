var map;
var polyline;
var control;

var totalDistance;
var totalDuration;
var totalTimeSeconds;

var messageField = document.getElementById("messages");
const saveToLocalButton = $('#saveToLocalButton');
const saveToServerButton = $('#saveToServerButton');


const locationList = $("#locationList");

var locationsById = {};

var markers = {};
var sub_markers = {};
var activePoints = [];

// Load locations to object

locations.forEach(function (location) {
    locationsById[location.pk] = location;
});

vehicles = [{
    vehicleName: "car",
    vehicleLabel: "Car"
}, {
    vehicleName: "bike",
    vehicleLabel: "Bike"
}
]

function createCheckbox(locationPK, type, label) {
    return `
    <input type="checkbox" id="${type}${locationPK}" name="location${locationPK}" class="is_${type}" data-location-id="${locationPK}">
    <label for="${type}${locationPK}">${label}</label><br>
    `;
}


function createDurationInput(locationPK) {
    return `<input type="number" style="width:100%" id="duration${locationPK}" name="duration${locationPK}" min="0" value="0" class="form-control"><br>`;
}

function createVehicleOptionSingle(vehicleName, vehicleLabel) {
    return `<option value="${vehicleName}">${vehicleLabel}</option>`;
}

function createVehicleOptionMulti(vehicles) {
    return vehicles.map(
        vehicle => createVehicleOptionSingle(vehicle.vehicleName, vehicle.vehicleLabel)
    ).join('');
}

function createVehicleOptions(locationPK, vehicles) {
    return `<select id="vehicle${locationPK}" style="width:100%" name="vehicle${locationPK}" class="form-control">
        ${createVehicleOptionMulti(vehicles)}
    </select>`;
}

// Functions for creating table cells
function createLocationCheckboxes(location) {
    return `
    <td style="width:5%">
        ${createCheckbox(location.pk, "anchor", "Anchor")}
        ${createCheckbox(location.pk, "sub", "Sub")}
    </td>`;
}

function createLocationVehicleDurationOption(location, vehicles) {
    return `
    <td style="width:5%">
        ${createDurationInput(location.pk)}
        ${createVehicleOptions(location.pk, vehicles)}
    </td>`;
}

// Function for creating a table row for a location
function createLocationRow(location, vehicles) {
    const bookmarkIconOpt = location.is_bookmarked ? 'fas' : 'far';
    return `
    <tr id="location${location.pk}">
        ${createLocationCheckboxes(location)}
        ${createLocationVehicleDurationOption(location, vehicles)}
        <td id="loc-name" style="width:15%">${location.name}</td>
        <td id="address" style="width:25%">${location.address}</td>
        <td style="width:5%">
            <i class='fa-star ${bookmarkIconOpt}' data-location-id='${location.pk}'></i>
        </td>
    </tr>`;
}

function updateLocationList(locations, vehicles) {
    locationList.empty();
    if (Object.keys(locations).length != 0) {
        $.each(locations, function (index, location) {
            locationList.append(createLocationRow(location, vehicles));
        });
    } else {
        locationList.append("<tr><td colspan='3'>No plan found.</td></tr>");
    }
}


const anchorOptions = {
    title: "",
    draggable: false,
    icon: L.icon({
        iconUrl: ankr_icon,
        iconSize: [40, 40], iconAnchor: [20, 40]
    })
}

const subsOptions = {
    title: "",
    draggable: false,
    icon: L.icon({
        iconUrl: subs_icon,
        iconSize: [40, 40], iconAnchor: [20, 40]
    })
}

function initMap() {
    map = L.map('map').setView([10.7327, 106.6998], 8);
    L.tileLayer(osmMapLink, {
        maxZoom: 19,
    }).addTo(map);
    polyline = L.polyline([], { color: 'red' }).addTo(map);
}

function createCircle(L, latLng, color = 'red', fillColor = '#f03', fillOpacity = 0.2, radius = 0) {
    // console.log(latLng);
    return L.circle(latLng, {
        color: color,
        fillColor: fillColor,
        fillOpacity: fillOpacity,
        radius: radius
    });
}

function createMarkerAndCircle(latLng, map, isAnchor) {
    var icon = isAnchor ? anchorOptions : subsOptions;

    var marker = L.marker(latLng, icon).addTo(map);

    if (isAnchor) {
        var circle = createCircle(L, latLng).addTo(map);
        return { marker: marker, circle: circle };
    } else {
        return { marker: marker };
    }
}

function addMarkerClickListener(locationId, isAnchor) {
    var marker;
    if (isAnchor) {
        marker = markers[locationId].marker;
    } else {
        marker = sub_markers[locationId].marker;
    }

    marker.on('click', function () {
        var latLngs = polyline.getLatLngs();
        var index = latLngs.findIndex(function (latLng) {
            return latLng.equals(marker.getLatLng());
        });
        if (index !== -1) {
            // The marker's location is already in the polyline, remove it
            latLngs.splice(index, 1);
            polyline.setLatLngs(latLngs);
        } else {
            // The marker's location is not in the polyline, add it
            polyline.addLatLng(marker.getLatLng());
        }
    });
}

function initAddMarkersEdit() {
    $('#planName').val(refillData.plan_name);
    // Set the value of the hidden input field when editing a plan
    $('#planId').val(refillData.plan_id);
    var matchLocationPk = [];
    refillData.location_waypoints.forEach(waypoint => {
        if (waypoint[1] == 1) {
            matchLocationPk.push(waypoint[0]);
        }
    });
    // console.log(locations);
    matchLocationPk.forEach(locPK => {
        var locationFound = locationsById[locPK];
        var latLng = L.latLng(locationFound.lat, locationFound.lng);
        handleAddMarker(locPK, latLng, map, true);
        polyline.addLatLng(latLng);
        $('#anchor' + locPK).prop('checked', true);
    })
}

function handleAddMarker(locationId, latLng, map, isAnchor) {
    if (isAnchor) {
        markers[locationId] = createMarkerAndCircle(latLng, map, true);
        addMarkerClickListener(locationId, true);
    } else {
        sub_markers[locationId] = createMarkerAndCircle(latLng, map, false);
        addMarkerClickListener(locationId, false);
    }
}

function removeMarker(locationId, map, markerList, isAnchor) {
    if (!markerList[locationId]) return false;

    if (markerList[locationId].marker) {
        map.removeLayer(markerList[locationId].marker);

        if (isAnchor) {
            map.removeLayer(markerList[locationId].circle);
        }
    }

    delete markerList[locationId];
}

function handleRemoveMarker(locationId, map, isAnchor) {
    if (isAnchor) return removeMarker(locationId, map, markers, true);
    return removeMarker(locationId, map, sub_markers, false);
}

function vehicleSpeed(vehicle) {
    switch (vehicle) {
        case 'car': return 60;
        case 'bike': return 40;
        default: return 0;
    }
}

function updateRadius() {
    // Get the location ID from the input/select field's id attribute
    var locationId = $(this).attr('id').replace(/(duration|vehicle)/, '');
    // Check if this location has an anchor marker
    if ($('#anchor' + locationId).is(':checked')) {
        // Get the duration and vehicle type
        var duration = $('#duration' + locationId).val() || 0;  // If the duration is empty, use 0
        var vehicle = $('#vehicle' + locationId).val();
        // Calculate the new radius based on the duration and vehicle type
        var speed = vehicleSpeed(vehicle) * 1000;
        var radius = speed * duration;

        // Update the radius of the circle
        markers[locationId].circle.setRadius(radius);
    }
}

function updateMessage(totalDistance, totalTimeSeconds) {
    messageField.innerHTML = `Distance: ${(totalDistance / 1000).toFixed(3)} km; Est duration: ${(totalTimeSeconds / 3600).toFixed(3)} hours.`;
}

function createControl(serviceUrl = osrmLink) {
    return L.Routing.control({
        waypoints: polyline.getLatLngs(),
        router: L.Routing.osrmv1({
            serviceUrl: serviceUrl,
            locs: function(i, waypoint) {
                return [waypoint.lng, waypoint.lat];
            }
        }),
        showAlternatives: false,
        lineOptions: {
            styles: [{ color: 'blue', opacity: 0.6, weight: 4 }]
        },
        instructions: {
            show: false
        }
    });
}

$(document).ready(function () {
    initMap();
    updateLocationList(locations, vehicles);
    if (refillData) {
        initAddMarkersEdit();
    }

    console.log($('#planId').val());

    $('.is_anchor, .is_sub').on('click', function () {
        var locationId = $(this).data('location-id');
        var location = locationsById[locationId];
        var latLng = L.latLng(location.lat, location.lng);
        var isAnchor = $(this).hasClass('is_anchor');
    
        if ($(this).is(':checked')) {
            // Clear other checkbox in the same row
            $(this).siblings('.is_sub, .is_anchor').prop('checked', false);
    
            // Remove existing marker if any
            handleRemoveMarker(locationId, map, true);
            handleRemoveMarker(locationId, map, false);
    
            // Add new marker
            handleAddMarker(locationId, latLng, map, isAnchor);
    
            // Add point to polyline immediately when checked
            polyline.addLatLng(latLng);
            activePoints.push(latLng);
            console.log("Added point to polyline:", latLng);
        } else {
            // Remove marker
            handleRemoveMarker(locationId, map, isAnchor);
    
            // Remove point from polyline
            var latLngs = polyline.getLatLngs();
            var index = latLngs.findIndex(function (point) {
                return point.equals(latLng);
            });
            if (index !== -1) {
                latLngs.splice(index, 1);
                polyline.setLatLngs(latLngs);
                activePoints.splice(index, 1);
            }
            console.log("Removed point from polyline:", latLng);
        }
    
        // Log current polyline points
        console.log("Current polyline points:", polyline.getLatLngs());
    });

    $('input[id^="duration"], select[id^="vehicle"]').on('input change', updateRadius);

    $('#createRouteButton').click(function () {
        console.log("clicked on create route");
        
        var waypoints = polyline.getLatLngs();
        console.log("Waypoints for routing:", waypoints);
        
        if (waypoints.length < 2) {
            alert("Please select at least 2 locations to create a route!");
            return;
        }
    
        if (control) {
            map.removeControl(control);
        }
    
        control = L.Routing.control({
            waypoints: waypoints,
            router: L.Routing.osrmv1({
                serviceUrl: osrmLink,
                locs: function(i, waypoint) {
                    return [waypoint.lng, waypoint.lat];
                }
            }),
            showAlternatives: false,
            lineOptions: {
                styles: [{ color: 'blue', opacity: 0.6, weight: 4 }]
            },
            instructions: {
                show: false
            }
        }).addTo(map);
    
        control.on('routesfound', function (e) {
            console.log("Route found:", e.routes);
            var routes = e.routes;
            window.routeData = routes;
            var summary = routes[0].summary;
    
            totalDistance = summary.totalDistance;
            totalTimeSeconds = summary.totalTime;
    
            updateMessage(totalDistance, totalTimeSeconds);
        });
    });

    saveToLocalButton.click(function () {
        if (window.routeData) {
            var blob = new Blob([
                JSON.stringify(window.routeData)],
                { type: "text/plain;charset=utf-8" }
            );
            saveAs(blob, "routeData.json");
        } else {
            alert("No routeData yet. Dig you forget to 'Create Route'?");
        }
    });

    saveToServerButton.click(function () {
        if (window.routeData) {
            makePostAjaxCallWithData(
                'save_route',
                JSON.stringify({
                    plan_id: $('#planId').val(),
                    plan_name: $('#planName').val(),
                    est_distance: totalDistance,
                    est_duration: totalTimeSeconds,
                    route_data: window.routeData,
                }),
                function () {
                    alert('Data successfully saved to the server. reload to make a new plan');
                },
                consoleLogError
            )
        } else {
            alert("No routeData yet. Did you forget to 'Create Route'?");
        }
    });

    $('#toggleLocations').on('click', function () {
        var button = $(this);

        if (button.text() === 'Hide Non-Bookmarked Locations') {
            // Loop over the locations
            for (var locationId in locationsById) {
                var location = locationsById[locationId];

                // If the location is not bookmarked, hide its corresponding row
                if (!location.is_bookmarked) {
                    $('#location' + locationId).hide();
                }
            }

            // Change the button text
            button.text('Show All Locations');
            button.removeClass('btn-primary').addClass('btn-success');
        } else {
            // Show all table rows
            $('tr').show();

            // Change the button text
            button.text('Hide Non-Bookmarked Locations');
            button.removeClass('btn-success').addClass('btn-primary');
        }
    });

});