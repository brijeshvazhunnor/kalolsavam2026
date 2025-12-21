from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.db.models import Count, Sum, Q
from django.utils.timezone import now
from django.views.decorators.cache import never_cache

from .forms import (
    LoginForm, RegisterForm, StudentForm,
    ItemForm, RegistrationForm
)
from .models import (
    Student, Item, Registration,
    College, Team, Result,
    CustomUser, SiteSetting, Brochure
)
from .utils import calculate_points

#homeeeeee
def home(request):
    return render(request, "accounts/home.html")

#👤 USER REGISTER
def user_register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


#🔐 LOGIN
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect


def user_login(request):
    """
    Single source of truth for login.
    DO NOT create any other login() view.
    """
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, "accounts/login.html")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account is disabled.")
                return render(request, "accounts/login.html")

            login(request, user)

            # 🔀 Role-based redirect
            if user.role == "college":
                return redirect("college_dashboard")
            elif user.role == "organizer":
                return redirect("organizer_dashboard")
            elif user.role == "admin":
                return redirect("admin_dashboard")

            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html")



#🚪 LOGOUT
def user_logout(request):
    logout(request)
    request.session.flush()
    return redirect("login")


#🎓 COLLEGE DASHBOARD
@login_required
def college_dashboard(request):
    if request.user.role != "college":
        return redirect("home")

    college = get_object_or_404(College, user=request.user)

    if request.method == "POST" and "add_student" in request.POST:
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.college = college
            student.save()
            messages.success(request, "Student added")
            return redirect("college_dashboard")
    else:
        form = StudentForm()

    return render(request, "accounts/register.html", {
        "student_form": form,
        "students": Student.objects.filter(college=college),
        "items": Item.objects.all(),
        "college": college,
    })


#🧑‍🎓 REGISTER STUDENT
@login_required
def register_student(request):
    if request.user.role != "college":
        return redirect("home")

    college = get_object_or_404(College, user=request.user)

    if request.method == "POST":
        Student.objects.create(
            college=college,
            name=request.POST["name"],
            id_card=request.POST["id_card"],
            date_of_birth=request.POST["date_of_birth"],
            department=request.POST["department"],
            year_of_joining=request.POST["year_of_joining"],
            current_year=request.POST["current_year"],
            id_card_file=request.FILES.get("id_card_file"),
        )
        messages.success(request, "Student registered")
        return redirect("register_student")

    return render(request, "accounts/register.html", {
        "students": Student.objects.filter(college=college),
        "college": college,
    })


#✏️ EDIT STUDENT
@login_required
def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == "POST":
        for field in [
            "name", "id_card", "date_of_birth",
            "department", "current_year", "year_of_joining"
        ]:
            setattr(student, field, request.POST.get(field))

        if request.FILES.get("id_card_file"):
            student.id_card_file = request.FILES["id_card_file"]

        student.save()
        messages.success(request, "Student updated")
        return redirect("register_student")

    return render(request, "accounts/edit_student.html", {"student": student})





#👥 TEAM CREATION (FIXED)
@login_required
def team_creation(request):
    if request.user.role != "college":
        return redirect("home")

    college = get_object_or_404(College, user=request.user)

    students = Student.objects.filter(college=college)
    items = Item.objects.all()
    categories = Item.objects.values_list("category", flat=True).distinct()

    existing_item_ids = Team.objects.filter(
        college=college
    ).values_list("item_id", flat=True)

    if request.method == "POST":
        item = get_object_or_404(Item, id=request.POST.get("item"))
        selected_students = request.POST.getlist("students")

        if Team.objects.filter(college=college, item=item).exists():
            messages.error(request, "Team already exists")
            return redirect("team_creation")

        team = Team.objects.create(
            college=college,
            item=item,
            category=item.category,
        )
        team.students.set(selected_students)
        messages.success(request, "Team created")
        return redirect("team_creation")

    return render(request, "team/create_team.html", {
        "students": students,
        "items": items,
        "categories": categories,
        "teams": Team.objects.filter(college=college),
        "existing_item_ids": existing_item_ids,
        "college": college,
    })


#edit team
@login_required
def edit_team(request, team_id):
    if request.user.role != "college":
        messages.error(request, "Only college users can edit teams.")
        return redirect("home")

    college = get_object_or_404(College, user=request.user)
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
                f"Maximum {item.max_participants} participants allowed for '{item.name}'."
            )
            return redirect("team_creation")

        single_limit = 4
        group_limit = 2

        for student_id in selected_students:
            student = Student.objects.get(id=student_id)

            single_count = (
                Team.objects.filter(
                    college=college,
                    students=student,
                    item__item_type="single",
                )
                .exclude(id=team.id)
                .count()
            )

            group_count = (
                Team.objects.filter(
                    college=college,
                    students=student,
                    item__item_type="group",
                )
                .exclude(id=team.id)
                .count()
            )

            if item.item_type == "single" and single_count >= single_limit:
                messages.error(
                    request,
                    f"{student.name} already reached {single_limit} single items."
                )
                return redirect("team_creation")

            if item.item_type == "group" and group_count >= group_limit:
                messages.error(
                    request,
                    f"{student.name} already reached {group_limit} group items."
                )
                return redirect("team_creation")

        team.students.set(selected_students)
        messages.success(request, f"Team '{item.name}' updated successfully.")
        return redirect("team_creation")

    return redirect("team_creation")



#🗑️ DELETE TEAM
@login_required
def delete_team(request, team_id):
    college = get_object_or_404(College, user=request.user)
    team = get_object_or_404(Team, id=team_id, college=college)
    team.delete()
    messages.success(request, "Team deleted")
    return redirect("team_creation")



#📊 STUDENT SUMMARY (FIXED)
@login_required
def student_summary(request):
    if request.user.role != "college":
        return redirect("home")

    college = get_object_or_404(College, user=request.user)

    # 🔎 GET FILTERS
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    item_type = request.GET.get("item_type", "").strip()

    students = Student.objects.filter(college=college)

    # 🔍 SEARCH FILTER (student name)
    if q:
        students = students.filter(name__icontains=q)

    student_data = []

    for student in students:
        teams = student.team_set.select_related("item")

        # 🎯 CATEGORY FILTER
        if category:
            teams = teams.filter(item__category=category)

        # 🎯 ITEM TYPE FILTER
        if item_type:
            teams = teams.filter(item__item_type=item_type)

        single = teams.filter(item__item_type="single").count()
        group = teams.filter(item__item_type="group").count()

        # ❗ Skip students with no teams after filtering
        if not teams.exists():
            continue

        student_data.append({
            "student": student,
            "single": single,
            "group": group,
            "total": single + group,
            "teams": teams,
        })

    return render(request, "college/student_summary.html", {
        "student_data": student_data,
        "categories": Item.objects.values_list("category", flat=True).distinct(),
        "selected_category": category,
        "selected_type": item_type,
        "q": q,
        "college": college,
    })








#Result committee Dashboard

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils.timezone import now

from .models import Item, Result, Team, College
from .utils import calculate_points
from django.views.decorators.cache import never_cache


from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

@never_cache
@login_required
def organizer_dashboard(request):
    return render(request, "organizer/dashboard.html", {
        "total_items": Item.objects.count(),
        "total_teams": Team.objects.count(),
        "total_results": Result.objects.filter(is_deleted=False).count(),
        "total_colleges": College.objects.count(),
    })


from django.db.models import Count, Q

@never_cache
@login_required
def organizer_items(request):
    q = request.GET.get("q", "")
    category = request.GET.get("category", "")
    status = request.GET.get("status", "")  # published / pending

    items = Item.objects.annotate(
        result_count=Count("results", filter=Q(results__is_deleted=False)),
        team_count=Count("team", distinct=True)
    )

    # 🔍 Search by event name
    if q:
        items = items.filter(name__icontains=q)

    # 🗂️ Filter by category
    if category:
        items = items.filter(category=category)

    # ✅ Filter by result status
    if status == "published":
        items = items.filter(result_count__gt=0)
    elif status == "pending":
        items = items.filter(result_count=0)

    total_items = items.count()
    published_items = items.filter(result_count__gt=0).count()
    pending_items = total_items - published_items

    # For dropdown
    categories = Item.objects.values_list("category", flat=True).distinct()

    return render(request, "organizer/items.html", {
        "items": items,
        "total_items": total_items,
        "published_items": published_items,
        "pending_items": pending_items,
        "categories": categories,
        "selected_category": category,
        "selected_status": status,
        "query": q,
    })


@never_cache
@login_required
def add_results(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    teams = Team.objects.filter(item=item).select_related("college")

    if request.method == "POST":
        Result.objects.filter(item=item).update(is_deleted=True)

        for team in teams:
            position = request.POST.get(f"position_{team.id}")
            grade = request.POST.get(f"grade_{team.id}")

            if position and grade:
                Result.objects.update_or_create(
                    item=item,
                    team=team,
                    defaults={
                        "position": int(position),
                        "grade": grade,
                        "points": calculate_points(int(position), grade),
                        "is_deleted": False,
                        "created_at": now(),
                    },
                )

        messages.success(request, "Results saved successfully")
        return redirect("organizer_items")

    return render(request, "organizer/add_results.html", {
        "item": item,
        "teams": teams,
    })

@never_cache
@login_required
def view_results(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    results = Result.objects.filter(item=item, is_deleted=False).select_related(
        "team__college"
    )
    return render(request, "organizer/view_results.html", {
        "item": item,
        "results": results,
    })

@never_cache
@login_required
def edit_result(request, result_id):
    result = get_object_or_404(Result, id=result_id)

    if request.method == "POST":
        position = int(request.POST["position"])
        grade = request.POST["grade"]

        result.position = position
        result.grade = grade
        result.points = calculate_points(position, grade)
        result.save()

        messages.success(request, "Result updated successfully")
        return redirect("view_results", item_id=result.item.id)

    return render(request, "organizer/edit_result.html", {
        "result": result,
        "position_choices": Result.POSITION_CHOICES,   # ✅ FIX
        "grade_choices": [g[0] for g in Result.GRADE_CHOICES],  # ✅ FIX
    })


@never_cache
@login_required
def delete_item_results(request, item_id):
    Result.objects.filter(item_id=item_id).update(is_deleted=True)
    messages.warning(request, "Results deleted (Undo available)")
    return redirect("organizer_items")

@never_cache
@login_required
def undo_delete_results(request, item_id):
    Result.objects.filter(item_id=item_id).update(is_deleted=False)
    messages.success(request, "Results restored")
    return redirect("organizer_items")

@never_cache
@login_required
def college_ranking_live(request):
    rankings = (
        Result.objects.filter(is_deleted=False)
        .values("team__college__college_name")
        .annotate(total_points=Sum("points"))
        .order_by("-total_points")
    )
    return render(request, "organizer/college_ranking.html", {"rankings": rankings})


from django.db.models import Q
@never_cache
@login_required
def organizer_student_results(request):
    query = request.GET.get("q", "")
    sort_by = request.GET.get("sort", "latest")

    results = Result.objects.filter(is_deleted=False).select_related(
        "item", "team__college"
    )

    # Search
    if query:
        results = results.filter(
            Q(team__college__college_name__icontains=query) |
            Q(item__name__icontains=query)
        )

    # Sorting
    if sort_by == "category":
        results = results.order_by("item__category", "item__name")

    elif sort_by == "college":
        results = results.order_by("team__college__college_name")

    elif sort_by == "student":
        # assuming Team has student_name or similar
        results = results.order_by("team__name")  # change if needed

    else:  # latest
        results = results.order_by("-created_at")

    return render(request, "organizer/student_results.html", {
        "results": results,
        "query": query,
        "sort_by": sort_by,
    })


#overall_result_views.py
#Leaderboard
#pointTable

from django.db.models import Sum, Q
from django.shortcuts import render
from .models import Result, Item


def public_results(request):
    category = request.GET.get("category", "").strip()
    q = request.GET.get("q", "").strip()

    # ---------------------------
    # Overall College Leaderboard
    # ---------------------------
    overall_colleges = (
        Result.objects
        .filter(is_deleted=False)
        .values("team__college__college_name")
        .annotate(total_points=Sum("points"))
        .order_by("-total_points")
    )

    # ---------------------------
    # Category-wise College Leaderboard
    # ---------------------------
    category_colleges = []
    if category:
        category_colleges = (
            Result.objects
            .filter(is_deleted=False, item__category__iexact=category)
            .values("team__college__college_name")
            .annotate(total_points=Sum("points"))
            .order_by("-total_points")
        )

    # ---------------------------
    # Top Individual Performers (Single Items)
    # ---------------------------
    individual_top = (
        Result.objects
        .filter(is_deleted=False, item__item_type="single")
        .values(
            "team__students__name",
            "team__college__college_name"
        )
        .annotate(total_points=Sum("points"))
        .order_by("-total_points")[:5]
    )

    # ---------------------------
    # FULL RESULT LIST
    # ---------------------------
    full_results = (
        Result.objects
        .filter(is_deleted=False)
        .select_related("item", "team__college")
        .prefetch_related("team__students")
        .order_by("-created_at")
    )

    # Search
    if q:
        full_results = full_results.filter(
            Q(item__name__icontains=q) |
            Q(item__category__icontains=q) |
            Q(team__college__college_name__icontains=q) |
            Q(team__students__name__icontains=q)
        )

    categories = Item.objects.values_list("category", flat=True).distinct()

    # ---------------------------
    # AJAX LIVE REFRESH
    # ---------------------------
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "results_live.html", {
            "overall_colleges": overall_colleges,
            "individual_top": individual_top,
            "full_results": full_results,
        })

    return render(request, "public_results.html", {
        "overall_colleges": overall_colleges,
        "category_colleges": category_colleges,
        "categories": categories,
        "selected_category": category,
        "individual_top": individual_top,
        "full_results": full_results,
        "q": q,
    })



#admin Dashboardddd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from .models import College, SiteSetting, Brochure

User = get_user_model()


def admin_only(user):
    return user.is_authenticated and user.role == "admin"


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not admin_only(request.user):
            messages.error(request, "Admin access only")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def admin_dashboard(request):
    if not admin_only(request.user):
        return redirect("home")

    return render(request, "admin/dashboard.html")


@login_required
def admin_users(request):
    if not admin_only(request.user):
        messages.error(request, "Access denied.")
        return redirect("home")

    users = User.objects.all().order_by("role", "username")

    # ✅ FIX: College linked via user FK
    college_map = {
        college.user.username: college.college_name
        for college in College.objects.select_related("user")
    }

    for u in users:
        if u.role == "college":
            u.college_display = college_map.get(u.username, "—")
        else:
            u.college_display = "—"

    return render(request, "admin/users.html", {
        "users": users
    })


@login_required
def admin_add_user(request):
    if not admin_only(request.user):
        messages.error(request, "Access denied.")
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        role = request.POST.get("role")
        college_name = request.POST.get("college_name", "").strip()
        district = request.POST.get("district", "").strip()

        if not username or not password or not role:
            messages.error(request, "All fields are required.")
            return redirect("admin_add_user")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("admin_add_user")

        # ✅ CREATE USER
        user = User.objects.create_user(
            username=username,
            password=password,
            role=role
        )

        # ✅ CREATE COLLEGE PROFILE IF ROLE = COLLEGE
        if role == "college":
            if not college_name:
                user.delete()
                messages.error(request, "College name is required.")
                return redirect("admin_add_user")

            College.objects.create(
                user=user,
                college_name=college_name,
                district=district,
            )

        messages.success(request, "User created successfully.")
        return redirect("admin_users")

    return render(request, "admin/add_user.html")



#🔁 ADMIN – ACTIVATE / DEACTIVATE USER
@login_required
def admin_toggle_user(request, user_id):
    if not admin_only(request.user):
        messages.error(request, "Access denied.")
        return redirect("admin_dashboard")

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.warning(request, "You cannot disable your own account.")
        return redirect("admin_users")

    user.is_active = not user.is_active
    user.save()

    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User '{user.username}' {status} successfully.")

    return redirect("admin_users")


#⚙️ ADMIN – SITE SETTINGS
@login_required
def admin_site_settings(request):
    if not admin_only(request.user):
        return redirect("home")

    setting, _ = SiteSetting.objects.get_or_create(id=1)

    if request.method == "POST":
        setting.allow_student_registration = "allow" in request.POST
        setting.save()
        messages.success(request, "Settings updated successfully.")

    return render(request, "admin/settings.html", {"setting": setting})


#📘 ADMIN – BROCHURES
@login_required
def admin_brochures(request):
    if not admin_only(request.user):
        return redirect("home")

    brochures = Brochure.objects.all()
    return render(request, "admin/brochures.html", {"brochures": brochures})



#➕ ADMIN – ADD BROCHURE
@login_required
def admin_add_brochure(request):
    if not admin_only(request.user):
        return redirect("home")

    if request.method == "POST":
        Brochure.objects.create(
            title=request.POST["title"],
            image=request.FILES["image"]
        )
        messages.success(request, "Brochure uploaded successfully.")
        return redirect("admin_brochures")

    return render(request, "admin/add_brochure.html")



#🌐 PUBLIC – BROCHURES
def public_brochures(request):
    brochures = Brochure.objects.filter(is_active=True)
    return render(request, "public/brochures.html", {
        "brochures": brochures
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()

@login_required
def admin_edit_user(request, user_id):
    if not admin_only(request.user):
        return redirect("home")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.username = request.POST.get("username", user.username)

        # ✅ CORRECT WAY
        if request.POST.get("password"):
            user.set_password(request.POST["password"])

        user.role = request.POST.get("role", user.role)
        user.save()

        messages.success(request, "User updated successfully.")
        return redirect("admin_users")

    return render(request, "admin/edit_user.html", {"u": user})


#Delete User

@login_required
def admin_delete_user(request, user_id):
    if not admin_only(request.user):
        messages.error(request, "Access denied.")
        return redirect("admin_dashboard")

    user = get_object_or_404(User, id=user_id)

    # ❌ Prevent self-delete
    if user == request.user:
        messages.warning(request, "You cannot delete your own account.")
        return redirect("admin_users")

    username = user.username
    user.delete()   # ✅ cascades College automatically

    messages.success(request, f"User '{username}' deleted successfully.")
    return redirect("admin_users")
