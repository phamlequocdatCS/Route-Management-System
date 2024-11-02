import json

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import (
    PERMISSIONS,
    STATUS_VALID_VALUES,
    Bookmark,
    Location,
    LoggerSystem,
    Note,
    Plan,
)
from .utilities.json_utils import (
    JSON_INSUFFICIENT_PERMISSION,
    json_return_error_status,
    json_return_success_status,
)


### Location
@login_required(login_url="home")
@require_GET
def search_loc(request):
    query = request.GET.get("q", "")
    n = request.GET.get("n")
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = None

    data = Bookmark.get_bookmarked_locations(request.user, n, query, True)

    return JsonResponse(data, safe=False, encoder=DjangoJSONEncoder)


def get_location_names(request):
    data = json.loads(request.body)
    location_names = []
    for coord in data:
        lat = coord["lat"]
        lng = coord["lng"]

        # Find the nearest location to the given coordinates
        location = Location.get_nearest(lat, lng)

        if location is None:
            location_names.append(f"({lat}, {lng})")
        else:
            location_names.append(location.name)

    return JsonResponse({"names": location_names})


@login_required(login_url="home")
@require_http_methods(["DELETE"])
def delete_location(request, location_id):
    return delete_object(request, location_id, Location)


### Note


@login_required(login_url="home")
@require_POST
def add_note(request):
    new_note = Note.create_note(
        request.user, request.POST.get("location_id"), request.POST.get("content")
    )

    if new_note is not None:
        new_note.save()
        return JsonResponse(json_return_success_status("Note", "added"))
    return JsonResponse(json_return_error_status("Location", "not found"))


@login_required(login_url="home")
@require_GET
def fetch_notes(request):
    data = json.dumps(
        Note.get_notes_by_loc(request.GET.get("location_id")),
        cls=DjangoJSONEncoder,
    )

    return JsonResponse(data, safe=False)


@login_required
@require_http_methods(["DELETE"])
def delete_note(request, note_id):
    return delete_object(request, note_id, Note)


### Bookmark


@login_required(login_url="home")
@require_POST
def bookmark_location(request):
    location = get_object_or_404(Location, pk=request.POST.get("location_id"))
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user, location=location
    )

    if not created:
        bookmark.delete()

    return JsonResponse({"bookmarked": created})


### Plan


@login_required(login_url="home")
@require_http_methods(["DELETE"])
def delete_route(request, plan_id):
    return delete_object(request, plan_id, Plan)


@login_required(login_url="home")
@require_POST
def save_route(request, id=None):
    data = json.loads(request.body)
    if id is None and (plan := Plan.create_from_json(request.user, data)):
        plan.save()
        new_log = LoggerSystem.create_plan_log(request.user, plan)
        print(new_log)
        new_log.save()
        return JsonResponse(json_return_success_status("Plan", "created"))
    if id is not None and (plan := Plan.objects.get(pk=id)):  # updating existing plan
        plan.update_plan(
            plan_name=data["plan_name"],
            est_distance=data["est_distance"],
            est_duration=data["est_duration"],
            route_data=data["route_data"],
        )
        new_log = LoggerSystem.create_edit_plan_log(request.user, plan)
        print(new_log)
        new_log.save()
        return JsonResponse(json_return_success_status("Plan", "edited"))
    return JsonResponse(json_return_error_status("Plan", "doesn't exist"))


@login_required(login_url="home")
def get_plan_route(request, plan_id):
    return JsonResponse(Plan.get_plan_data_by_id(plan_id))


@login_required(login_url="home")
@require_POST
def update_plan_status(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    if plan:
        old_status = plan.status
        new_status = request.POST.get("status")
        if new_status not in STATUS_VALID_VALUES:
            return JsonResponse(json_return_error_status("Plan status", "invalid", 400))
        if new_status == old_status:
            return JsonResponse(
                json_return_error_status("Plan status", "was not changed", 400)
            )

        if request.user.has_perm(PERMISSIONS.CAN_UPDATE_PLAN_STATUS, plan):
            plan.status = new_status
            plan.save()

            new_log = LoggerSystem.create_update_plan_status_log(
                request.user, plan, old_status, new_status
            )
            print(new_log)
            new_log.save()

            return JsonResponse(json_return_success_status("Plan", "updated"))
        return JsonResponse(
            json_return_error_status("Plan", "is completed, cannot be edited", 400)
        )
    return JsonResponse(json_return_error_status("Plan", "does not exist", 404))


def delete_object(request, obj_id, model):
    try:
        obj = model.objects.get(pk=obj_id)

        save_log = True

        if isinstance(obj, Plan):
            if not request.user.has_perm(PERMISSIONS.CAN_DELETE_PLAN, obj):
                return JsonResponse(JSON_INSUFFICIENT_PERMISSION)

        if isinstance(obj, Location):
            if not request.user.has_perm(PERMISSIONS.CAN_DELETE_LOC):
                return JsonResponse(JSON_INSUFFICIENT_PERMISSION)

        if isinstance(obj, Note):
            if not request.user.has_perm(PERMISSIONS.CAN_DELETE_NOTE, obj):
                return JsonResponse(JSON_INSUFFICIENT_PERMISSION)
            save_log = False

        if save_log:
            new_log = LoggerSystem.create_delete_obj_log(
                user=request.user, obj=obj, obj_type=model.__name__
            )
            new_log.save()
            print(new_log)

        obj.delete()

        return JsonResponse({"status": "success"})

    except model.DoesNotExist:
        return JsonResponse(json_return_error_status(model.__name__, "not found"))
