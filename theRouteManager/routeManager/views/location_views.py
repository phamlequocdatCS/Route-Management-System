import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

from ..forms import EditLocationForm
from ..models import PERMISSIONS, Location, LoggerSystem
from ..utilities.json_utils import (
    JSON_INSUFFICIENT_PERMISSION,
    json_return_error_status,
    json_return_success_status,
)


@login_required(login_url="home")
def display_locations(request):
    return render(request, "lookup_loc.html")


@login_required(login_url="home")
def add_loc_view(request):
    if request.user.has_perm(PERMISSIONS.CAN_ADD_LOC):
        if request.method == "POST":
            data = json.loads(request.body)
            location = Location.create_from_json(data)
            if location:
                location.save()
                new_log = LoggerSystem.create_add_loc_log(request.user, location)
                new_log.save()
                print(new_log)
                return JsonResponse(json_return_success_status("Location", "added"))
        return render(request, "add_loc.html")
    return JsonResponse(JSON_INSUFFICIENT_PERMISSION)


@login_required(login_url="home")
def edit_loc_view(request, location_id):
    print("I am called")
    location = get_object_or_404(Location, pk=location_id)
    
    if not request.user.has_perm(PERMISSIONS.CAN_EDIT_LOC, location):
        return JsonResponse(JSON_INSUFFICIENT_PERMISSION)


    if request.method == "POST":
        old_name = location.name
        old_addr = location.address
        form = EditLocationForm(request.POST, instance=location)
        if form.is_valid():
            message = process_edit_location_form_log(
                request.user, location, form, old_name, old_addr
            )
            return create_edit_loc_form_log(message)
        else:
            return JsonResponse(
                json_return_error_status("Location", "cannot be updated")
            )

    form = EditLocationForm(instance=location)
    form_html = form_html_builder(
        "editLocationForm", f"edit_location/{location_id}/", form
    )
    return JsonResponse({"form_html": form_html})


def form_html_builder(id, action, form):
    return f'<form id="{id}" action="{action}" method="post">{form.as_p()}</form>'


def process_edit_location_form_log(user, location, form, old_name, old_addr):
    new_name = form.cleaned_data.get("name")
    new_addr = form.cleaned_data.get("address")
    message = []
    if new_name != old_name:
        message.append("name")
        create_edit_loc_log(user, location, "name", old_name, new_name)
    if new_addr != old_addr:
        message.append("address")
        create_edit_loc_log(user, location, "address", old_addr, new_addr)
    form.save()
    return message


def create_edit_loc_form_log(message):
    if len(message) == 0:
        return JsonResponse(
            json_return_success_status("Location data same,", "nothing was updated")
        )
    if len(message) == 1:
        message = message[0]
    else:
        message = " and ".join(message)
    return JsonResponse(json_return_success_status(f"Location {message}", "updated"))


def create_edit_loc_log(user, location, field, old_val, new_val):
    """Create an edit location log for the given user and location and what is changed."""
    new_log = LoggerSystem.create_edit_loc_log(
        user=user,
        location=location,
        field_name=field,
        old_value=old_val,
        new_value=new_val,
    )
    new_log.save()
    print(new_log)
