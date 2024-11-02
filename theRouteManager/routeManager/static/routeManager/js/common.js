const managerRole = 'mngr';
const ownerRole = 'ownr';

const osmMapLink = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
// const osrmLink = 'https://router.project-osrm.org/route/v1';
const osrmLink = 'http://127.0.0.1:5000/route/v1';
const nominatimAutocompleteLink = 'https://nominatim.openstreetmap.org/search?format=json&countrycodes=vn&q='

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

