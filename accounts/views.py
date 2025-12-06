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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import College, Student, Item, Team


@login_required
def team_creation(request):
    # Only colleges can access
    if request.user.role != "college":
        messages.error(request, "Only college users can create teams.")
        return redirect("home")

    college = get_object_or_404(College, username=request.user.username)

    students = Student.objects.filter(college=college).order_by("name")
    items = Item.objects.all().order_by("category", "name")
    categories = Item.objects.values_list('category', flat=True).distinct().order_by('category')

    # for front-end: which items already have a team for this college
    existing_item_ids = list(
        Team.objects.filter(college=college).values_list("item_id", flat=True)
    )

    if request.method == "POST":
        item_id = request.POST.get("item")
        selected_students = request.POST.getlist("students")

        if not item_id:
            messages.error(request, "Please select an event item.")
            return redirect("team_creation")

        item = get_object_or_404(Item, id=item_id)

        # Check if team already exists for this item
        if Team.objects.filter(college=college, item=item).exists():
            messages.error(
                request,
                f"You have already created a team for '{item.name}'. You can edit it below."
            )
            return redirect("team_creation")

        if not selected_students:
            messages.error(request, "Please select at least one student.")
            return redirect("team_creation")

        if len(selected_students) > item.max_participants:
            messages.error(
                request,
                f"Maximum {item.max_participants} participants are allowed for '{item.name}'."
            )
            return redirect("team_creation")

        team = Team.objects.create(
            college=college,
            item=item,
            category=item.category
        )
        team.students.set(selected_students)
        messages.success(request, f"Team for '{item.name}' created successfully.")
        return redirect("team_creation")

    teams = (
        Team.objects.filter(college=college)
        .select_related("item")
        .prefetch_related("students")
        .order_by("item__category", "item__name")
    )

    context = {
        "students": students,
        "items": items,
        "categories": categories,
        "teams": teams,
        "existing_item_ids": existing_item_ids,
    }
    return render(request, "team/create_team.html", context)


from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

@login_required
def delete_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)

    if team.college.username != request.user.username:
        messages.error(request, "You are not allowed to delete this team.")
        return redirect("team_creation")

    team.delete()
    messages.success(request, "Team deleted successfully.")
    return redirect("team_creation")



@login_required
def edit_team(request, team_id):
    if request.user.role != "college":
        messages.error(request, "Only college users can edit teams.")
        return redirect("home")

    college = get_object_or_404(College, username=request.user.username)
    team = get_object_or_404(Team, id=team_id, college=college)
    item = team.item

    if request.method == "POST":
        selected_students = request.POST.getlist("edit_students")

        if not selected_students:
            messages.error(request, "A team must have at least one participant.")
            return redirect("team_creation")

        if len(selected_students) > item.max_participants:
            messages.error(
                request,
                f"Maximum {item.max_participants} participants are allowed for '{item.name}'."
            )
            return redirect("team_creation")

        team.students.set(selected_students)
        messages.success(request, f"Team for '{item.name}' updated successfully.")
        return redirect("team_creation")

    return redirect("team_creation")




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
