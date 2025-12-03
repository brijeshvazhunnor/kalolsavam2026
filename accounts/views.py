from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, RegisterForm, StudentForm, ItemForm, RegistrationForm
from .models import Student, Item, Registration, College, Team


# ---------------- Homepage ----------------
def home(request):
    return render(request, 'accounts/home.html')


# ---------------- User Registration ----------------
def user_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


# ---------------- User Login ----------------
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from accounts.models import College, CustomUser

def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()

        # Check if the login is for a college user
        college = College.objects.filter(username=username, password=password).first()

        if college:
            # Convert College login → Django session using CustomUser
            user = CustomUser.objects.filter(username=username).first()
            if not user:
                # If CustomUser does not exist, create it (role = college)
                user = CustomUser.objects.create_user(
                    username=username,
                    password=password,
                    role="college",
                    college_name=college.college_name
                )
            login(request, user)
            return redirect("college_dashboard")

        # If not college → normal Django authentication
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.role == "organizer":
                return redirect("organizer_dashboard")
            if user.role == "admin":
                return redirect("admin_dashboard")
            return redirect("home")

        messages.error(request, "Invalid username or password")
        return redirect("login")

    return render(request, "accounts/login.html")





# ---------------- Logout ----------------
def user_logout(request):
    logout(request)
    return redirect("login")


# ---------------- College Dashboard ----------------
@login_required
def college_dashboard(request):
    if request.user.role != "college":
        return redirect("home")

    # Get the College record of this logged college user
    college = College.objects.filter(username=request.user.username).first()
    if not college:
        messages.error(request, "College profile missing.")
        return redirect("home")

    if request.method == "POST" and "add_student" in request.POST:
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.college = college     # ✔ correct college assignment
            student.save()
            messages.success(request, "Student added successfully!")
            return redirect("college_dashboard")
    else:
        form = StudentForm()

    students = Student.objects.filter(college=college)
    items = Item.objects.all()

    return render(request, "accounts/register.html", {
        "student_form": form,
        "students": students,
        "items": items,
    })


# ---------------- Register Student (from sidebar page) ----------------
@login_required
def register_student(request):
    if request.user.role != "college":
        return redirect("home")

    college = College.objects.filter(username=request.user.username).first()
    if not college:
        messages.error(request, "College profile missing.")
        return redirect("home")

    if request.method == "POST":
        Student.objects.create(
            college=college,
            name=request.POST.get("name"),
            id_card=request.POST.get("id_card"),
            date_of_birth=request.POST.get("date_of_birth"),
            department=request.POST.get("department"),
            year_of_joining=request.POST.get("year_of_joining"),
            current_year=request.POST.get("current_year"),
            id_card_file=request.FILES.get("id_card_file")
        )
        messages.success(request, "Student registered successfully!")
        return redirect("register_student")

    students = Student.objects.filter(college=college).order_by("-id")
    return render(request, "accounts/register.html", {"students": students})


#-----------------------------Edit Student______________________
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

@login_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        student.name = request.POST.get("name")
        student.id_card = request.POST.get("id_card")
        student.date_of_birth = request.POST.get("date_of_birth")
        student.department = request.POST.get("department")
        student.current_year = request.POST.get("current_year")
        student.year_of_joining = request.POST.get("year_of_joining")

        if request.FILES.get("id_card_file"):
            student.id_card_file = request.FILES.get("id_card_file")

        student.save()
        messages.success(request, "Student details updated successfully!")
        return redirect("register_student")

    return render(request, "accounts/edit_student.html", {"student": student})




# ---------------- Create Team ----------------
def team_creation(request):
    college = College.objects.get(username=request.user.username)
    students = Student.objects.filter(college=college)
    items = Item.objects.all()

    # extract distinct category list
    categories = Item.objects.values_list("category", flat=True).distinct()

    teams = Team.objects.filter(college=college).select_related("item").prefetch_related("students")

    return render(request, "team/create_team.html", {
        "students": students,
        "items": items,
        "categories": categories,
        "teams": teams,
    })




#dummmy
@login_required
def organizer_dashboard(request):
    if request.user.role != "organizer":
        return redirect("home")
    return render(request, "organizer/dashboard.html")

@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect("home")
    return render(request, "admin/dashboard.html")
