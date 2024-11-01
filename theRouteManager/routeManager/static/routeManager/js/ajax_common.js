function consoleLogError(error) {
    console.log('Error:', error);
}

function alertError(error) {
    alert(error);
}

function makeAjaxCall(url, options) {
    const defaultOptions = {
        url: url,
        dataType: 'json',
        success: options.successFn,
        error: options.errorFn
    };

    $.ajax({...defaultOptions, ...options});
}

function makeGetAjaxCallWithId(objId, url, successFn, errorFn) {
    makeAjaxCall(url + '/' +  objId + '/', { type: 'GET', successFn, errorFn });
}

function makeGetAjaxCallWithData(url, data, successFn, errorFn) {
    makeAjaxCall(url, { type: 'GET', data, successFn, errorFn });
}

function makeDeleteAjaxCallWithId(objId, url, successFn, errorFn) {
    makeAjaxCall(url + '/' +  objId + '/', {
        type: 'DELETE', 
        headers: {'X-CSRFToken': getCookie('csrftoken')}, 
        successFn, 
        errorFn 
    });
}

function makePostAjaxCallWithData(url, data, successFn, errorFn) {
    makeAjaxCall(url, {
        type: 'POST', 
        data, 
        contentType: 'application/json', 
        beforeSend: function(xhr) { xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken')); }, 
        successFn, 
        errorFn
    });
}

function makePostAjaxCallWithDataNoContentType(url, data, successFn, errorFn) {
    makeAjaxCall(url, {
        type: 'POST', 
        data, 
        beforeSend: function(xhr) { xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken')); }, 
        successFn, 
        errorFn
    });
}

function makePostAjaxCallWithDataNoCSRF(url, data, successFn, errorFn) {
    makeAjaxCall(url, { 
        type: 'POST', 
        data, 
        dataType: 'json', 
        successFn, 
        errorFn
    });
}

function fetchFromUrl(url, terms, successFn, errorFn) {
    makeAjaxCall(url + terms, { 
        type: 'GET', 
        successFn, 
        errorFn 
    });
}
