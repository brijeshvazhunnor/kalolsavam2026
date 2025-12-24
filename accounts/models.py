from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


# ---------------------------------------------------------
# Custom User
# ---------------------------------------------------------
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('college', 'College'),
        ('organizer', 'Organizer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='college')
    college_name = models.CharField(max_length=255, blank=True, null=True)

    REQUIRED_FIELDS = ["email"]
    USERNAME_FIELD = "username"

    def __str__(self):
        return self.username



# ---------------------------------------------------------
# College Table
# ---------------------------------------------------------
from django.conf import settings

class College(models.Model):
    user = models.ForeignKey(   # 🔥 TEMP: NOT OneToOne
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="colleges"
    )
    college_name = models.CharField(max_length=255)
    district = models.CharField(max_length=255)

    def __str__(self):
        return self.college_name




# ---------------------------------------------------------
# Student Model
# ---------------------------------------------------------
def student_upload_path(instance, filename):
    return f"students/{instance.college.college_name}/{instance.id_card}/{filename}"

class Student(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    id_card = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    department = models.CharField(max_length=255)
    year_of_joining = models.IntegerField()
    current_year = models.IntegerField()

    id_card_file = models.FileField(upload_to=student_upload_path, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.college.college_name})"



# ---------------------------------------------------------
# Item Model (Event Items)
# ---------------------------------------------------------
from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=255)
    numbers = models.PositiveIntegerField()
    category = models.CharField(max_length=255)
    max_participants = models.PositiveIntegerField(default=1)
    item_type = models.CharField(max_length=10, choices=[("single","single"),("group","group")])  # ← added





# ---------------------------------------------------------
# Participation (student → item)
# ---------------------------------------------------------
class Participation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} in {self.item.name}"

class Registration(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student.name} → {self.item.name}"

class Team(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    category = models.CharField(max_length=255)
    students = models.ManyToManyField(Student)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} - {self.college.college_name}"



from django.db import models
from django.utils.timezone import now
from .models import Item, Team  # ensure Item & Team imported correctly


class Result(models.Model):
    POSITION_CHOICES = [
        (1, "1st"),
        (2, "2nd"),
        (3, "3rd"),
    ]

    GRADE_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("E", "E"),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="results")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="results")

    position = models.PositiveSmallIntegerField(choices=POSITION_CHOICES)
    grade = models.CharField(max_length=1, choices=GRADE_CHOICES, default="E")
    points = models.IntegerField(default=0)

    # soft delete
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=now)

    class Meta:
        unique_together = ("item", "team")
        ordering = ["position", "-points"]

    def __str__(self):
        return f"{self.item.name} — {self.team.college.college_name}"


#admin Models
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# -------------------------
# GLOBAL SITE SETTINGS
# -------------------------
class SiteSetting(models.Model):
    allow_student_registration = models.BooleanField(default=True)

    def __str__(self):
        return "Global Site Settings"


# -------------------------
# BROCHURES
# -------------------------
class Brochure(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="brochures/")
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# accounts/models.py

class AppealNotification(models.Model):
    STATUS_CHOICES = (
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    college = models.ForeignKey(College, on_delete=models.CASCADE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    position = models.PositiveSmallIntegerField(
        choices=Result.POSITION_CHOICES,
        null=True,
        blank=True
    )
    grade = models.CharField(
        max_length=1,
        choices=Result.GRADE_CHOICES,
        null=True,
        blank=True
    )

    message = models.TextField(blank=True)
    result_image = models.ImageField(
        upload_to="appeal_results/",
        null=True,
        blank=True
    )

    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_appeals"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.item.name} – {self.college.college_name} ({self.status})"
