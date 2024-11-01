map = L.map('osm-map').setView([10.7327, 106.6998], 13);
    
L.tileLayer(osmMapLink, {}).addTo(map);

function fetchLocationSuccess(json) {
    return $.map(json, function(item) {
        return {
            label: item.display_name,
            value: item.display_name,
            lat: item.lat,
            lon: item.lon,
            type: item.class + ', ' + item.type
        };
    });
}

$("#search").autocomplete({
    source: function(request, response) {
        fetchFromUrl(
            nominatimAutocompleteLink,
            request.term,
            function(json) {
                response(fetchLocationSuccess(json));
            },
            consoleLogError
        )
    },
    select: function(event, ui) {
        var coords = [ui.item.lat, ui.item.lon];
        map.setView(coords, 13);
        L.marker(coords).addTo(map);

        // Update the selectedLocation variable
        selectedLocation = {
            lat: ui.item.lat,
            lng: ui.item.lon,
            name: ui.item.value,
            address: ui.item.label,
            type: ui.item.type
        };
    }
});

$('#save-location').click(function() {
    if (selectedLocation) {
        makePostAjaxCallWithData(
            'add_loc_view', 
            JSON.stringify({
                lat: selectedLocation.lat,
                lng: selectedLocation.lng,
                name: selectedLocation.name,
                address: selectedLocation.address,
                location_type: selectedLocation.type,
            }),
            function(data) {
                if (data.status === 'success') {
                    alert(data.message);
                } else {
                    alert('An error occurred while saving the data: ' + data.error);
                }
            },
            alertError
        )
    }
});