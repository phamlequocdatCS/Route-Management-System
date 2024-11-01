from django.contrib.auth.decorators import login_required
import json
from ..models import Location, Plan, PERMISSIONS, Bookmark
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse

from ..utilities.json_utils import (
    json_return_error_status,
    JSON_INSUFFICIENT_PERMISSION,
)


@login_required(login_url="home")
def planner(request, id=None):
    if id is None and request.user.has_perm(PERMISSIONS.CAN_ADD_PLAN):
        data = json.dumps(
            Bookmark.get_bookmarked_locations(request.user, None, "", True),
            cls=DjangoJSONEncoder,
        )
        return render(
            request,
            "planner.html",
            {"locations_json": data, "current_user": request.user},
        )
    if id is not None and request.user.has_perm(PERMISSIONS.CAN_EDIT_PLAN):
        plan = Plan.objects.get(pk=id)
        if isinstance(plan, Plan) and request.user.has_perm(
            PERMISSIONS.CAN_EDIT_PLAN, plan
        ):
            data = json.dumps(
                Bookmark.get_bookmarked_locations(request.user, None, "", True),
                cls=DjangoJSONEncoder,
            )
            return edit_plan(request, plan, data)
        return JsonResponse(
            json_return_error_status("Plan", "is completed, cannot be edited", 400)
        )
    return JsonResponse(JSON_INSUFFICIENT_PERMISSION)


def edit_plan(request, plan: Plan, data):
    locations_waypoints = Location.parse_osm_route(plan.route_data)
    refill_data = {
        "plan_id": plan.pk,
        "plan_name": plan.plan_name,
        "location_waypoints": locations_waypoints,
    }
    refill_data_json = json.dumps(refill_data, cls=DjangoJSONEncoder)
    return render(
        request,
        "planner.html",
        {
            "locations_json": data,
            "current_user": request.user,
            "refill_data": refill_data_json,
        },
    )
