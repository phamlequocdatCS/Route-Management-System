var directionsService;
var directionsRenderer;
var map;
var mapObjects;

const planList = $("#planList");

const statusStyles = {
    'Pending': 'secondary',
    'Accepted': 'info',
    'Rejected': 'danger',
    'Canceled': 'dark',
    'In-progress': 'primary',
    'Complete': 'success'
};

const statusOptions = [
    { value: 'pendng', label: 'Pending' },
    { value: 'accept', label: 'Accepted' },
    { value: 'reject', label: 'Rejected' },
    { value: 'cancel', label: 'Canceled' },
    { value: 'progrs', label: 'In-progress' },
    { value: 'complt', label: 'Complete' }
];

function buildButtonWithObjData(btnClass, btnBootstrapType, objDataName, objPk, btnLabel, planStatus) {
    var statusAttribute = planStatus ? `data-plan-status='${planStatus}'` : '';
    return `
        <button class='${btnClass} btn btn-${btnBootstrapType}' data-${objDataName}='${objPk}' ${statusAttribute}>${btnLabel}</button>
    `;
}


function createPlanRow(plan) {
    var buttons = buildButtonWithObjData('view-plan', 'primary', 'plan-id', plan.pk, 'View plan');

    var statusBlock = `<span class="badge badge-${statusStyles[plan.status]} custom-badge">${plan.status}</span>`;

    if (currentUserRole === ownerRole || currentUserRole === managerRole) {
        buttons += buildButtonWithObjData('edit-plan', 'warning', 'plan-id', plan.pk, 'Edit plan', plan.status);
        buttons += buildButtonWithObjData('delete-plan', 'danger', 'plan-id', plan.pk, 'Delete plan', plan.status);

        if (plan.status !== 'Complete') {
            var options = statusOptions.map(function (option) {
                var selected = plan.status === option.label ? 'selected' : '';
                return `<option value="${option.value}" ${selected}>${option.label}</option>`;
            }).join('');

            statusBlock = `<select class="change-status custom-select" data-plan-id='${plan.pk}'>${options}</select>`;
        }

    }

    return `
        <tr>
            <td> ${plan.plan_name} </td>
            <td> ${plan.username} </td>
            <td> ${(plan.est_distance / 1000).toFixed(3)} km</td>
            <td> ${(plan.est_duration / 3600).toFixed(3)} hr</td>
            <td> ${statusBlock} </td>
            <td> ${buttons} </td>
        </tr>`;
}


function updatePlanList(plans) {
    planList.empty();
    if (Object.keys(plans).length != 0) {
        $.each(plans, function (index, plan) {
            planList.append(createPlanRow(plan));
        });
    } else {
        planList.append("<tr><td colspan='3'>No plan found.</td></tr>");
    }
}

function displayPlan(planId) {
    makeGetAjaxCallWithId(
        planId, 'get_plan_route', planGetSuccess, consoleLogError
    )
}

function planGetSuccess(data) {
    // Show the container div
    var container = document.getElementById('container');
    container.style.display = 'flex';

    var viewControl = document.getElementById('viewControl');

    viewControl.style.display = 'flex';

    // If the map already exists, remove it
    if (map) map.remove();

    // Create a Leaflet map
    map = L.map('map').setView([
        data.route_data[0].waypoints[0].latLng.lat, data.route_data[0].waypoints[0].latLng.lng
    ], 13);



    // Add a tile layer to the map
    L.tileLayer(osmMapLink, {
        maxZoom: 19,
    }).addTo(map);

    // Create a polyline from the route data and add it to the map
    var latlngs = data.route_data[0].coordinates.map(function (coordinate) {
        return [coordinate.lat, coordinate.lng];
    });
    // Create a polyline with renderer option set to L.canvas()
    var polyline = L.polyline(latlngs, { renderer: L.canvas() }).addTo(map);

    // Add markers for the waypoints
    data.route_data[0].waypoints.forEach(function (waypoint) {
        L.marker([waypoint.latLng.lat, waypoint.latLng.lng]).addTo(map);
    });

    var coordinates = getWaypointCoordinates(data.route_data[0].waypoints);

    // Add information to the info box
    var infoBox = document.getElementById('info');
    infoBox.innerHTML = ''; // Clear the info box

    infoBox.innerHTML = buildRouteInfoDisplay(data.route_data[0]);
    makePostAjaxCallWithData(
        getLocationName, JSON.stringify(coordinates),
        function (data) {
            infoBox.innerHTML += "<p><b>Waypoints</b></p>";
            infoBox.innerHTML += buildWaypointNames(data.names);
        },
        function (error) {
            console.error('An error occurred:', error);
        }
    )

    container.scrollIntoView(true);

}



$('#closeView').click(function () {
    var container = document.getElementById('container');
    container.style.display = 'none';

    var viewControl = document.getElementById('viewControl');
    viewControl.style.display = 'none';

});

var loadingDiv = document.getElementById('loading');
$('#saveImage').click(function () {
    loadingDiv.style.display = 'flex';
    console.log(loadingDiv.style);
    leafletImage(map, function (err, canvas1) {
        var container = $('#info');
        container.css('backgroundColor', '#fff');

        var originalFontFamily = container.css('font-family');
        container.css('font-family', 'Helvetica Neue, sans-serif');

        var orderedListItems = container.find('ol li');
        orderedListItems.each(function (index) {
            $(this).data('original', $(this).html());
            $(this).html((index + 1) + '. ' + $(this).text());
        });

        var unorderedListItems = container.find('ul li');
        var bullet = "•";
        unorderedListItems.each(function (index) {
            $(this).data('original', $(this).html());
            $(this).html(bullet + ' ' + $(this).data('original'));
        });

        html2canvas(container[0], { backgroundColor: '#fff', useCORS: true }).then(function (canvas2) {
            var finalCanvas = document.createElement('canvas');
            finalCanvas.width = canvas1.width + canvas2.width;
            finalCanvas.height = Math.max(canvas1.height, canvas2.height);

            var context = finalCanvas.getContext('2d');
            context.drawImage(canvas1, 0, 0);
            context.drawImage(canvas2, canvas1.width, 0);

            var link = document.createElement('a');
            link.download = 'combined.png';
            link.href = finalCanvas.toDataURL();
            $(link).get(0).click();
            loadingDiv.style.display = 'none';

            container.css('font-family', originalFontFamily);

            orderedListItems.each(function () {
                $(this).html($(this).data('original'));
            });
            unorderedListItems.each(function () {
                $(this).html($(this).data('original'));
            });
        });
    });

});


function getWaypointCoordinates(waypoints) {
    var coordinates = [];
    waypoints.forEach(element => {
        coordinates.push(element.latLng);
    });
    return coordinates;
}

function buildWaypointNames(waypointNames) {
    var output = "<ol>";
    waypointNames.forEach(waypointName => {
        output += `
            <li>${waypointName}</li>
        `
    });

    output += "</ol>";
    return output;
}

function calculateRouteCost(numWayPoints, distance, time) {
    const perWaypointFee = 50_000;
    const timeFee = 523_000;
    const gasFee = 23_000;
    const carFee = 500_000;
    const humanFee = 500_000;

    var gasCost = (distance / 100) * 5;

    var cost = time * timeFee + gasCost * gasFee + numWayPoints * perWaypointFee + carFee + humanFee;

    return cost;
}

function buildRouteInfoDisplay(route_data) {
    var numWayPoints = route_data.waypoints.length;

    var distance = route_data.summary.totalDistance / 1000;
    var time = route_data.summary.totalTime / 3600;

    var cost = calculateRouteCost(numWayPoints, distance, time);

    var formattedCost = cost.toLocaleString('en-US', { style: 'currency', currency: 'VND' });

    return `
    <h2>Route Information</h2>
    <ul>
        <li>
            <b>Summary:</b> ${route_data.name}
        </li>
        <li>
            <b>Distance:</b> ${distance.toFixed(3)} km
        </li>
        <li>
            <b>Duration:</b> ${time.toFixed(3)} hr
        </li>
        <li>
            <b>Estimate price:</b> ${formattedCost}
        </li>
    </ul>
    `
}

function planDeleteSuccess(data) {
    if (data.status == 'success') {
        alert('Plan deleted successfully');
        window.location.reload();
    } else {
        alert(data.error);
    }
};

$(document).ready(function () {
    updatePlanList(plans);

    $(document).on('click', '.view-plan', function () {
        displayPlan($(this).data('plan-id'));
    });

    $(document).on('click', '.delete-plan', function () {
        makeDeleteAjaxCallWithId(
            $(this).data('plan-id'), 'delete_route',
            planDeleteSuccess, alertError
        );
    });

    $(document).on('change', '.change-status', function () {
        var planId = $(this).data('plan-id');
        var newStatus = $(this).val();

        // Add a confirmation dialog when the user selects the 'Complete' option
        if (newStatus === 'complt') {
            var confirmAction = confirm('Are you sure you want to mark this as complete? This action is irreversible.');
            if (!confirmAction) {
                // If the user cancels the confirmation, reset the select value to its previous value
                $(this).val($(this).data('prev-status'));
                return;
            }
        }
        makePostAjaxCallWithDataNoContentType(
            'update_plan_status/' + planId + '/', {
            'status': newStatus
        },
            function (data) {
                if (data.error) {
                    alert('An error occurred:', data.error);
                } else {
                    alert('Plan updated successfully');
                }
            },
            alertError
        )
    }).on('focus', '.change-status', function () {
        // Store the previous value when the select element receives focus
        $(this).data('prev-status', $(this).val());
    });

    $(document).on('click', '.edit-plan', function () {
        var planId = $(this).data('plan-id');
        var planStatus = $(this).data('plan-status');
        console.log(planStatus);
        if (planStatus !== 'Complete') {
            window.location.href = 'planner/' + planId;
        } else {
            alert('This plan is completed and cannot be edited.');
        }
    });
});
