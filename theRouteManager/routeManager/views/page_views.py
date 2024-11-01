import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from ..models import Log, Plan


def home_view(request):
    return render(request, "home.html")


@login_required(login_url="home")
def view_logs(request):
    logs = Log.objects.all().order_by("-timestamp")
    return render(request, "view_logs.html", {"logs": logs})


@login_required(login_url="home")
def view_plans(request):
    return render(
        request,
        "view_plans.html",
        {"plans_json": json.dumps(Plan.get_plans()), "current_user": request.user},
    )
