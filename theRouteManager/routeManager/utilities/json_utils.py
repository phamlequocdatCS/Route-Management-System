JSON_INSUFFICIENT_PERMISSION = {"status": "error", "error": "Insufficient permissions"}


def json_return_success_status(model, action):
    """`{'status': 'success', 'message': f'{model} {action} successfully'}`"""
    return {"status": "success", "message": f"{model} {action} successfully"}


def json_return_error_status(model=None, action=None, error_code=None):
    """default = `{'status': 'error', 'error': f'Form is invalid'}`"""
    if model is None:
        model = "Form"
    if action is None:
        action = "is invalid data"
    if error_code is None:
        error_code = "error"
    return {"status": error_code, "error": f"{model} {action}"}
