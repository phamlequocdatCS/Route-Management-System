import numpy as np
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import JSONField, Q

from .calculations import calculate_ball_tree, nearest_loc_index
from .utilities.utils import generate_ssn, generate_username, process_json


class ROLE(models.TextChoices):
    OWNER = "ownr", "Owner"
    MANAGER = "mngr", "Manager"
    OPERATOR = "oper", "Operator"


class STATUS(models.TextChoices):
    PENDNG = "pendng", "Pending"
    ACCEPT = "accept", "Accepted"
    REJECT = "reject", "Rejected"
    CANCEL = "cancel", "Canceled"
    PROGRS = "progrs", "In-progress"
    COMPLT = "complt", "Complete"


STATUS_VALID_VALUES = dict(STATUS.choices)


class PLAN_CLEARANCE(models.TextChoices):
    CONFIDENTIAL = "cfdt", "Is confidential"
    OPEN = "open", "Is open"


class ACTION(models.TextChoices):
    CREATE = "crt", "Created"
    UPDATE = "upd", "Updated"
    DELETE = "del", "Deleted"
    LOGIN = "lgn", "Logged In"
    LOGOUT = "lgt", "Logged Out"
    NONE = "non", "None"


class PERMISSIONS:
    CAN_CREATE_ACCOUNT = "can_create_acc"
    CAN_ADD_LOC = "can_add_loc"
    CAN_EDIT_LOC = "can_edit_loc"
    CAN_DELETE_LOC = "can_delete_loc"

    CAN_ADD_PLAN = "can_add_route"
    CAN_EDIT_PLAN = "can_edit_plan"
    CAN_DELETE_PLAN = "can_edit_plan"
    CAN_VIEW_PLAN = "can_view_plan"
    CAN_UPDATE_PLAN_STATUS = "can_update_plan_status"

    CAN_ADD_NOTE = "can_add_note"
    CAN_EDIT_NOTE = "can_edit_note"
    CAN_DELETE_NOTE = "can_delete_note"

    CAN_UN_BOOKMARK = "can_un_bookmark"

    UNIVERSAL_PERMS = [CAN_ADD_LOC, CAN_ADD_PLAN, CAN_ADD_NOTE, CAN_EDIT_LOC]


class JSON_FIELDS:
    LOCATION = ["lat", "lng", "name", "address", "location_type"]
    PLAN = ["plan_name", "est_distance", "est_duration", "route_data"]


class MyAccountManager(BaseUserManager):
    def create_user(
        self,
        email: str | None = None,
        password: str | None = None,
        full_name: str | None = None,
        username: str | None = None,
        user_role: tuple[str, str] | None = None,
        ssn: str | None = None,
    ) -> "Account":
        """Create and return a new user."""
        if not email:
            raise ValueError("Users must have an email address")

        if username is None:
            username = generate_username(email)
        if user_role is None:
            user_role = ROLE.OPERATOR
        if ssn is None:
            ssn = generate_ssn()

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            full_name=full_name,
            ssn=ssn,
            user_role=user_role,
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(
        self, email=None, username: str | None = None, password: str | None = None
    ) -> "Account":
        """Create and return a new superuser."""
        if username is None:
            username = "godmode"

        if password is None:
            raise ValueError("Superusers must have a password")

        email = f"{username}@superuser.com"
        ssn = generate_ssn()
        user = self.create_user(email, password, username, username, ROLE.OWNER, ssn)
        user.is_admin = user.is_staff = user.is_superuser = user.is_active = True
        user.save(using=self._db)

        return user


class Account(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(verbose_name="username", max_length=20, unique=True)
    full_name = models.CharField(
        verbose_name="full name", max_length=60, unique=False, null=True
    )
    ssn = models.CharField(verbose_name="ssn", max_length=9, unique=True, null=True)

    user_role = models.CharField(
        max_length=4, choices=ROLE.choices, default=ROLE.OPERATOR
    )

    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # False in production
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)

    objects = MyAccountManager()

    USERNAME_FIELD = "username"

    def __repr__(self) -> str:
        return f"{self.username} [{self.user_role}] | {self.email} | {self.full_name} | {self.ssn}"

    def __str__(self):
        return self.__repr__()

    def has_perm(self, perm, obj=None):
        """Check if the user has a specific permission."""

        if self.user_role == ROLE.OWNER:
            return True

        if perm in PERMISSIONS.UNIVERSAL_PERMS:
            return True

        if isinstance(obj, Plan) and (output := self._plan_perms(perm, obj)):
            return output

        if isinstance(obj, Note):
            print(obj.author)
            print(self)
            if (
                perm in [PERMISSIONS.CAN_EDIT_NOTE, PERMISSIONS.CAN_DELETE_NOTE]
                and obj.author == self
            ):
                return True

        if perm == PERMISSIONS.CAN_UN_BOOKMARK and isinstance(obj, Bookmark):
            return obj.user == self

        if self.user_role == ROLE.MANAGER:
            return perm in [
                # Location
                PERMISSIONS.CAN_DELETE_LOC,
            ]

        return False

    def has_module_perms(self, app_label):
        """Does this user have permission to view this app? (ALWAYS YES FOR SIMPLICITY)"""
        return True

    def _plan_perms(self, perm, obj: "Plan"):
        if (
            perm == PERMISSIONS.CAN_VIEW_PLAN
            and self.user_role == ROLE.OPERATOR
            and obj.clearance == PLAN_CLEARANCE.OPEN
        ):
            return True

        if perm == PERMISSIONS.CAN_EDIT_PLAN and obj.status == STATUS.PENDNG:
            return self.user_role == ROLE.MANAGER or obj.user == self

        if perm == PERMISSIONS.CAN_UPDATE_PLAN_STATUS:
            return obj.status != STATUS.COMPLT and self.user_role == ROLE.MANAGER

        if perm == PERMISSIONS.CAN_DELETE_PLAN:
            if self.user_role == ROLE.MANAGER:
                return obj.status != STATUS.COMPLT

        return None


class Location(models.Model):
    location_id = models.AutoField(primary_key=True)
    lat = models.FloatField()
    lng = models.FloatField()
    name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    location_type = models.CharField(max_length=255, blank=True, null=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"({self.lat}, {self.lng}) {self.name} @ {self.address}"

    def is_bookmarked_by(self, user: Account | None = None):
        if user is None:
            return False
        return Bookmark.objects.filter(user=user, location=self).exists()

    def serialize(self, user):
        return {
            "pk": str(self.pk),
            "lat": self.lat,
            "lng": self.lng,
            "name": self.name,
            "address": self.address,
            "location_type": self.location_type,
            "is_bookmarked": self.is_bookmarked_by(user),
            "modified_at": self.modified_at,
        }

    @staticmethod
    def get_nearest(lat, lng, max_distance_meters=200):
        locations = list(Location.objects.all())
        location_coords = np.radians(
            [(location.lat, location.lng) for location in locations]
        )

        tree = calculate_ball_tree(location_coords)
        distances, indices = tree.query(
            [np.radians([float(lat), float(lng)])], return_distance=True
        )

        nearest_index = nearest_loc_index(distances, indices, max_distance_meters)
        if nearest_index is not None:
            return locations[nearest_index]
        return None

    @staticmethod
    def parse_osm_route(route_data):
        waypoints = route_data[0]["waypoints"]
        waypoint_coords = [
            (waypoint["latLng"]["lat"], waypoint["latLng"]["lng"])
            for waypoint in waypoints
        ]
        locations_waypoints = []
        for lat, lng in waypoint_coords:
            found_location = Location.get_nearest(lat, lng)
            if isinstance(found_location, Location):
                locations_waypoints.append((found_location.location_id, 1))
            else:
                locations_waypoints.append(((lat, lng), -1))

        return locations_waypoints

    @staticmethod
    def create_from_json(data):
        try:
            return Location(**process_json(data, JSON_FIELDS.LOCATION))
        except Exception as e:
            print(e)
            return None


class Bookmark(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return (
            f"{self.user.username} bookmarked {self.location.name} @ {self.created_at}"
        )

    def __str__(self):
        return self.__repr__()

    @staticmethod
    def get_bookmarked_locations(user, n=None, query="", sort_bookmark=False):
        if query:
            locations = Location.objects.filter(
                Q(name__icontains=query) | Q(address__icontains=query)
            )
        else:
            locations = Location.objects.all()

        locations = locations.order_by("-modified_at")
        loc_w_bookmark = [loc.serialize(user) for loc in locations]
        loc_w_bookmark.sort(key=lambda x: x["modified_at"], reverse=True)
        if sort_bookmark:
            # If sort_bookmark is True, sort by is_bookmarked first and then by date modified
            loc_w_bookmark.sort(key=lambda x: x["is_bookmarked"], reverse=True)

        # Limit the number of locations returned
        if n is not None:
            loc_w_bookmark = loc_w_bookmark[:n]

        return loc_w_bookmark


class Note(models.Model):
    author = models.ForeignKey(Account, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return f"Note by {self.author.username} on {self.location.name} @ {self.created_at}"

    def __str__(self):
        return self.__repr__()

    def serialize(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at,
            "author": self.author.username,
            "location": self.location.name,
        }

    @staticmethod
    def create_note(user: Account, location_id: int, content: str):
        location = Location.objects.get(location_id=location_id)
        new_note = None
        if location:
            new_note = Note(author=user, location=location, content=content)

        return new_note

    @staticmethod
    def get_notes_by_loc(location_id: int):
        location = Location.objects.get(location_id=location_id)
        loc_notes = []
        notes = Note.objects.filter(location=location)
        if location:
            loc_notes = [note.serialize() for note in notes]

        return loc_notes


class Plan(models.Model):
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    plan_name = models.CharField(max_length=255, blank=True, null=True)
    est_distance = models.FloatField(blank=True, null=True)
    est_duration = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=6, choices=STATUS.choices, default=STATUS.PENDNG
    )
    route_data = JSONField(blank=True, null=True)
    clearance = models.CharField(
        max_length=4, choices=PLAN_CLEARANCE.choices, default=PLAN_CLEARANCE.OPEN
    )

    def __repr__(self) -> str:
        return f"{self.plan_name}, created by {self.username} @ {self.created_at}"

    def __str__(self):
        return self.__repr__()
    
    def serialize(self):
        return {
            'pk': self.pk,  
            'plan_name': self.plan_name, 
            'username' : self.user.username,
            'est_distance' : self.est_distance,
            'est_duration' : self.est_duration,
            'status' : self.get_status_display(),
        }

    def update_plan(
        self,
        plan_name=None,
        est_distance=None,
        est_duration=None,
        created_at=None,
        route_data=None,
    ):
        if plan_name is not None:
            self.plan_name = plan_name
        if est_distance is not None:
            self.est_distance = est_distance
        if est_duration is not None:
            self.est_duration = est_duration
        if created_at is not None:
            self.created_at = created_at
        if route_data is not None:
            self.route_data = route_data
        self.save()

    @staticmethod
    def get_plans(order="status"):
        plans = Plan.objects.order_by(order)
        return {str(plan.pk): plan.serialize() for plan in plans}

    @staticmethod
    def get_plan_data_by_id(plan_id: int):
        plan = Plan.objects.get(pk=plan_id)
        return {"route_data": plan.route_data}

    @staticmethod
    def create_from_json(user: Account, data):
        try:
            return Plan(user=user, **process_json(data, JSON_FIELDS.PLAN))
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def get_plan_and_update_status(user: Account, plan_id: int):
        if user.has_perm(PERMISSIONS.CAN_UPDATE_PLAN_STATUS):
            plan = Plan.objects.get(pk=plan_id)
            return plan
        return None


class Log(models.Model):
    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=255)
    action = models.CharField(max_length=3, choices=ACTION.choices, default=ACTION.NONE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey("content_type", "object_id")

    field_name = models.CharField(max_length=255, null=True)
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __repr__(self):
        return f"{self.username} {self.get_action_display()} a {self.content_type} | {self.field_name} at {self.timestamp}"

    def __str__(self):
        return self.__repr__()


class LoggerSystem:
    @staticmethod
    def create_login_log(user: Account):
        print(type(user))
        return Log(
            user=user, username=user.username, action=ACTION.LOGIN, content_object=user
        )

    @staticmethod
    def create_logout_log(user: Account):
        return Log(
            user=user, username=user.username, action=ACTION.LOGOUT, content_object=user
        )

    @staticmethod
    def create_add_loc_log(user: Account, location: Location):
        return Log(
            user=user,
            username=user.username,
            action=ACTION.CREATE,
            content_object=location,
        )

    @staticmethod
    def create_edit_loc_log(
        user: Account, location: Location, field_name, old_value, new_value
    ):
        return Log(
            user=user,
            username=user.username,
            action=ACTION.UPDATE,
            content_object=location,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    def create_plan_log(user: Account, plan: Plan):
        return Log(
            user=user, username=user.username, action=ACTION.CREATE, content_object=plan
        )

    @staticmethod
    def create_update_plan_status_log(
        user: Account, plan: Plan, old_status, new_status
    ):
        return Log(
            user=user,
            username=user.username,
            action=ACTION.UPDATE,
            content_object=plan,
            field_name="status",
            old_value=old_status,
            new_value=new_status,
        )

    @staticmethod
    def create_edit_plan_log(user: Account, plan: Plan):
        return Log(
            user=user,
            username=user.username,
            action=ACTION.UPDATE,
            content_object=plan,
            field_name="plan information",
        )

    @staticmethod
    def create_delete_obj_log(user: Account, obj, obj_type):
        return Log(
            user=user,
            username=user.username,
            action=ACTION.DELETE,
            content_object=obj,
            field_name="whole object",
            old_value=f"{obj_type} with info={obj}",
        )
