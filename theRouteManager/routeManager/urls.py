from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from . import api
from .views import authentication_views, location_views, page_views, routing_views

BASE_ROUTE = "routeManager"


urlpatterns = [
    path("admin/", admin.site.urls),
    # Password reset
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path("password_reset/", authentication_views.password_reset_view, name="password_reset"),
    path("password_reset/done/", page_views.home_view, name="password_reset_done"),
    path("reset/done/", page_views.home_view, name="password_reset_complete"),
    # Register
    path(f"{BASE_ROUTE}/register", authentication_views.account_create_view, name="register"),
    ### VIEWS ###
    # Home and logins
    path(f"{BASE_ROUTE}/home", page_views.home_view, name="home"),
    path(f"{BASE_ROUTE}/", authentication_views.login_view, name="login"),
    path(f"{BASE_ROUTE}/logout", authentication_views.logout_view, name="logout"),
    # Location
    path(f"{BASE_ROUTE}/add_loc_view", location_views.add_loc_view, name="add_loc_view"),
    path(f"{BASE_ROUTE}/lookup_loc", location_views.display_locations, name="lookup_loc"),
    # Plan
    path(f"{BASE_ROUTE}/view_plans", page_views.view_plans, name="view_plans"),
    path(f"{BASE_ROUTE}/planner", routing_views.planner, name="planner"),
    path(f"{BASE_ROUTE}/planner/<int:id>/", routing_views.planner, name="planner"),
    # Logs
    path(f"{BASE_ROUTE}/view_logs", page_views.view_logs, name="view_logs"),
    ###########
    ### API ###
    ###########
    # Bookmark API
    path(f"{BASE_ROUTE}/bookmark_location", api.bookmark_location, name="bookmark_location"),
    # Location API
    path(f"{BASE_ROUTE}/search", api.search_loc, name="search"),
    path(
        f"{BASE_ROUTE}/delete_location/<int:location_id>/",
        api.delete_location,
        name="delete_location",
    ),
    path(
        f"{BASE_ROUTE}/edit_location/<int:location_id>/",
        location_views.edit_loc_view,
        name="edit_location",
    ),
    path(
        f"{BASE_ROUTE}/get_location_names",
        api.get_location_names,
        name="get_location_names",
    ),
    # Note API
    path(f"{BASE_ROUTE}/fetch_notes", api.fetch_notes, name="fetch_notes"),
    path(f"{BASE_ROUTE}/add_note", api.add_note, name="add_note"),
    path(f"{BASE_ROUTE}/delete_note/<int:note_id>/", api.delete_note, name="delete_note"),
    # Plan API
    path(f"{BASE_ROUTE}/save_route", api.save_route, name="save_route"),
    path(f"{BASE_ROUTE}/planner/<int:id>/save_route", api.save_route, name="save_route"),
    path(
        f"{BASE_ROUTE}/get_plan_route/<int:plan_id>/",
        api.get_plan_route,
        name="get_plan_route",
    ),
    path(f"{BASE_ROUTE}/delete_route/<int:plan_id>/", api.delete_route, name="delete_route"),
    path(
        f"{BASE_ROUTE}/update_plan_status/<int:plan_id>/",
        api.update_plan_status,
        name="update_plan_status",
    ),
]
