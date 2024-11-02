const viewNoteModal = $('#viewNotesModal');
const addNoteModal = $('#addNoteModal');
const addNoteModalLabel = $('#addNoteModalLabel')
const viewNotesModalLabel = $('#viewNotesModalLabel')
const locationList = $("#locationList");
const locationCount = $("#locationCount")
const notesList = $('#notesList');

var currentLocationSelected;

function formatDateModified(dateRaw) {
    // Create a new Date object from the date string
    var date = new Date(dateRaw);

    // Format the date
    return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

}

function createLocationRow(location) {
    return `
        <tr>
            <td>${location.name}</td>
            <td>${location.address}</td>
            <td>${formatDateModified(location.modified_at)}</td>
            <td>
                <i class='fa-star ${location.is_bookmarked ? "fas" : "far"}' data-location-id='${location.pk}'></i>
                <button class='view-notes btn btn-info' data-location-id='${location.pk}'>View Notes</button>
                <button class='add-note btn btn-secondary' data-location-id='${location.pk}'>Add Note</button>
                <button class='edit-location btn btn-warning' data-location-id='${location.pk}'>Edit Location</button>
                <button class='delete-location btn btn-danger' data-location-id='${location.pk}'>Delete Location</button>
            </td>
        </tr>`;
};

function updateLocationList(locations) {
    locationList.empty();
    if (locations.length > 0) {
        $.each(locations, function (index, location) {
            locationList.append(createLocationRow(location));
        });
    } else {
        locationList.append("<tr><td colspan='3'>No locations found.</td></tr>");
    }

    // Update the location count text
    locationCount.text(`Showing ${locations.length} locations...`);
};

function createDeleteNoteButton(username, author, note_id) {
    if (username === author) {
        console.log("Nice");
        return `<button class='delete-note btn btn-danger' data-note-id='${note_id}'>Delete Note</button>`;
    }
    return "";
}

function createNoteElement(note) {
    console.log(note);
    return `
        <div style="border: 1px solid #ddd; margin-bottom: 10px; padding: 10px;">
            <h4>${note.content}</h4>
            <p>By ${note.author} on ${new Date(note.created_at).toLocaleDateString()}</p>
            ${createDeleteNoteButton(username, note.author, note.id)}
        </div>`;
};

function fetchLocations(query, n = 10) {
    makeGetAjaxCallWithData(
        searchURL, {
        'q': query,
        'n': n
    },
        updateLocationList,
        alertError
    )
};

function updateNotesList(notes) {
    notesList.empty();
    if (notes.length > 0) {
        $.each(notes, function (index, note) {
            notesList.append(createNoteElement(note));
        });
    } else {
        notesList.append("<p>No notes found.</p>");
    }
    viewNoteModal.modal('show');
};

function handleBookmarkedIcon(icon, data) {
    if (data.bookmarked) {
        icon.removeClass('far').addClass('fas');
    } else {
        icon.removeClass('fas').addClass('far');
    }
};

function handleNoteAdd(data) {
    if (data.status == 'success') {
        alert(data.message);
        addNoteModal.modal('hide');
    } else {
        alert('Failed to add note. ' + data.error);
    }
};

function handleDeleteBookmark(data) {
    if (data.status == 'success') {
        alert('Location deleted successfully');
        window.location.reload();
    } else {
        alert(data.error);
    }
}

function fetchNotes(locationId) {
    makeGetAjaxCallWithData(
        fetchNotesURL, {
        'location_id': locationId
    },
        function (data) {
            updateNotesList(JSON.parse(data));
        },
        alertError
    )
}

$(document).ready(function () {
    // Get CSRF token
    var csrftoken = jQuery("[name=csrfmiddlewaretoken]").val();

    // Set up AJAX to use CSRF token
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Perform an initial AJAX call when the page loads
    fetchLocations('');

    // Search functionality
    $("#searchBox").on("keyup", function () {
        var query = $(this).val();
        fetchLocations(query);
    });

    // View all locations
    $("#searchAllButton").on("click", function () {
        fetchLocations('', null);
    });

    // Handle the "View Notes" action
    $(document).on('click', '.view-notes', function () {
        currentLocationSelected = $(this).data('location-id');
        fetchNotes(currentLocationSelected);
        var locationName = $(this).closest('tr').children('td:first').text();
        viewNotesModalLabel.text('View notes for ' + locationName);
    });

    // Handle the "Add Note" action
    $(document).on('click', '.add-note', function () {
        var locationId = $(this).data('location-id');
        var locationName = $(this).closest('tr').children('td:first').text();
        addNoteModal.data('location-id', locationId);  // Store the location ID in the modal
        addNoteModalLabel.text('Add note to ' + locationName);  // Update the modal title
        addNoteModal.modal('show');  // Show the modal
    });

    // Handle the "Save Note" action in the modal
    $('#saveNote').click(function () {
        makePostAjaxCallWithDataNoCSRF(
            addNoteURL, {
            'location_id': addNoteModal.data('location-id'),
            'content': $('#noteContent').val()
        },
            handleNoteAdd,
            alertError
        )
    });

    // Bookmark functionality
    $(document).on('click', '.fa-star', function () {
        var icon = $(this);
        makePostAjaxCallWithDataNoCSRF(
            bookmarkURL, {
            'location_id': icon.data('location-id')
        },
            function (data) {
                handleBookmarkedIcon(icon, data);
            },
            alertError
        )
    });

    // Delete location functionality
    $(document).on('click', '.delete-location', function () {
        var userConfirmed = confirm('Are you sure you want to delete this location?');
        if (userConfirmed) {
            makeDeleteAjaxCallWithId(
                $(this).data('location-id'),
                'delete_location',
                handleDeleteBookmark,
                alertError
            );
        }
    });

    // Edit location functionality
    $(document).on('click', '.edit-location', function () {
        var locationId = $(this).data('location-id');
        var editLocationURL = `edit_location/${locationId}/`;
        $.get(editLocationURL, function (data) {
            $('#editLocationModal .modal-body').html(data.form_html);
            $('#editLocationModal').modal('show');
        });
    });

    // Save the location edit
    $('#saveChangesButton').on('click', function () {
        var form = $('#editLocationModal form');
        var editLocationURL = form.attr('action');
        console.log(editLocationURL);
        var formData = form.serialize();
        makePostAjaxCallWithDataNoCSRF(
            editLocationURL,
            formData,
            function (data) {
                if (data.status === 'success') {
                    $('#editLocationModal').modal('hide');
                    alert(data.message);
                    fetchLocations('');
                } else {
                    alert('An error occurred while saving the data: ' + data.error);
                }
            },
            consoleLogError
        )
    });

    // Delete note
    $(document).on('click', '.delete-note', function () {
        var userConfirmed = confirm('Are you sure you want to delete this note?');
        if (userConfirmed) {
            console.log(this);
            makeDeleteAjaxCallWithId(
                $(this).data('note-id'), 'delete_note',
                function (data) {
                    console.log(data);
                    alert("Note deleted successfully");
                    fetchNotes(currentLocationSelected);
                }, function (data) { alert(data.error); }
            );
        }
    });

});