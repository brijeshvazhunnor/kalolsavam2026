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
class College(models.Model):
    college_name = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)   # plain password from CSV

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
    max_participants = models.PositiveIntegerField(default=1)  # ADD THIS

    def __str__(self):
        return self.name



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
