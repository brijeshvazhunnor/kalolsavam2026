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
# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from .models import College, Student, Item, Team


@login_required
def team_creation(request):
    """Create team with:
       - per-student single/group limits
       - per-category team limits
       - special Natakam sub-limit inside Drishyanatakolsavam
    """
    if request.user.role != "college":
        messages.error(request, "Only college users can create teams.")
        return redirect("home")

    college = get_object_or_404(College, username=request.user.username)

    students = Student.objects.filter(college=college).order_by("name")
    items = Item.objects.all().order_by("category", "name")
    categories = (
        Item.objects.values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    # Items that already have a team for this college
    existing_item_ids = list(
        Team.objects.filter(college=college).values_list("item_id", flat=True)
    )

    # ---------- CATEGORY LIMIT INFO FOR UI ----------
    # Expected in settings.py:
    # CATEGORY_LIMITS = {
    #   "sahithyolsavam": 27,
    #   "chithrolsavam": 9,
    #   "sangeetholsavam": 17,
    #   "nritholsavam": 12,
    #   "drishyanatakolsavam": 8,
    # }
    category_limits_cfg = getattr(settings, "CATEGORY_LIMITS", {})
    category_limits = []

    for key, limit in category_limits_cfg.items():
        used = Team.objects.filter(
            college=college,
            category__iexact=key,
        ).count()
        category_limits.append(
            {
                "key": key,
                "label": key.capitalize(),
                "used": used,
                "limit": limit,
                "remaining": max(limit - used, 0),
                "percent": (used / limit * 100) if limit > 0 else 0,
            }
        )

    # Natakam special info for UI
    natakam_items = getattr(settings, "NATAKAM_ITEMS", [])
    max_natakam = getattr(settings, "MAX_NATAKAM", 2)
    natakam_count = Team.objects.filter(
        college=college,
        item__name__in=natakam_items,
    ).count()
    # ------------------------------------------------

    if request.method == "POST":
        item_id = request.POST.get("item")
        selected_students = request.POST.getlist("students")

        if not item_id:
            messages.error(request, "Please select an event item.")
            return redirect("team_creation")

        item = get_object_or_404(Item, id=item_id)
        category = item.category.lower()

        # 1️⃣ Team duplicate check
        if Team.objects.filter(college=college, item=item).exists():
            messages.error(
                request,
                f"You already created a team for '{item.name}'. Edit it below.",
            )
            return redirect("team_creation")

        # 2️⃣ Category limit check
        current_category_count = Team.objects.filter(
            college=college,
            category__iexact=category,
        ).count()
        allowed_limit = category_limits_cfg.get(category, 99999)

        if current_category_count >= allowed_limit:
            messages.error(
                request,
                f"Category limit reached! You can create only {allowed_limit} "
                f"teams in {item.category}."
            )
            return redirect("team_creation")

        # 3️⃣ Natakam sub-limit inside Drishyanatakolsavam
        if category == "drishyanatakolsavam" and item.name in natakam_items:
            if natakam_count >= max_natakam:
                messages.error(
                    request,
                    "You can create only "
                    f"{max_natakam} Natakam teams "
                    f"({', '.join(natakam_items)}).",
                )
                return redirect("team_creation")

        # 4️⃣ No student selected
        if not selected_students:
            messages.error(request, "Please select at least one student.")
            return redirect("team_creation")

        # 5️⃣ Max participants for the item
        if len(selected_students) > item.max_participants:
            messages.error(
                request,
                f"Maximum {item.max_participants} students allowed for "
                f"'{item.name}'."
            )
            return redirect("team_creation")

        # 6️⃣ Per-student single/group limits
        single_limit = 4
        group_limit = 2

        for student_id in selected_students:
            student = Student.objects.get(id=student_id)

            single_count = Team.objects.filter(
                college=college,
                students=student,
                item__item_type="single",
            ).count()

            group_count = Team.objects.filter(
                college=college,
                students=student,
                item__item_type="group",
            ).count()

            if item.item_type == "single" and single_count >= single_limit:
                messages.error(
                    request,
                    f"❌ {student.name} already reached the limit of "
                    f"{single_limit} single items.",
                )
                return redirect("team_creation")

            if item.item_type == "group" and group_count >= group_limit:
                messages.error(
                    request,
                    f"❌ {student.name} already reached the limit of "
                    f"{group_limit} group items.",
                )
                return redirect("team_creation")

        # 7️⃣ CREATE TEAM — all validations passed
        team = Team.objects.create(
            college=college,
            item=item,
            category=item.category,
        )
        team.students.set(selected_students)
        messages.success(request, f"Team for '{item.name}' created successfully.")
        return redirect("team_creation")

    # Load teams for UI
    teams = (
        Team.objects.filter(college=college)
        .select_related("item")
        .prefetch_related("students")
        .order_by("item__category", "item__name")
    )

    return render(
        request,
        "team/create_team.html",
        {
            "students": students,
            "items": items,
            "categories": categories,
            "teams": teams,
            "existing_item_ids": existing_item_ids,
            "category_limits": category_limits,
            "natakam_count": natakam_count,
            "max_natakam": max_natakam,
        },
    )


@login_required
def edit_team(request, team_id):
    """Edit team with same student limit rules (single/group) kept."""
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
                f"Maximum {item.max_participants} participants allowed for "
                f"'{item.name}'.",
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
                    f"❌ {student.name} already reached the limit of "
                    f"{single_limit} single items.",
                )
                return redirect("team_creation")

            if item.item_type == "group" and group_count >= group_limit:
                messages.error(
                    request,
                    f"❌ {student.name} already reached the limit of "
                    f"{group_limit} group items.",
                )
                return redirect("team_creation")

        team.students.set(selected_students)
        messages.success(request, f"Team for '{item.name}' updated successfully.")
        return redirect("team_creation")

    return redirect("team_creation")




@login_required
def delete_team(request, team_id):
    """Delete a team belonging to this college."""
    if request.user.role != "college":
        messages.error(request, "Only college users can delete teams.")
        return redirect("home")

    college = get_object_or_404(College, username=request.user.username)
    team = get_object_or_404(Team, id=team_id, college=college)
    item_name = team.item.name
    team.delete()
    messages.success(request, f"Team for '{item_name}' deleted successfully.")
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



#Result committee Dashboard

POSITION_POINTS = {1: 5, 2: 3, 3: 1}
GRADE_POINTS = {"A": 3, "B": 2, "C": 1, "D": 0, "E": 0}


# accounts/views.py (part with organizer features)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Sum, Count
from django.urls import reverse

from .models import Item, Team, Result, Student, College

# scoring maps
POSITION_POINTS = {1: 5, 2: 3, 3: 1}
GRADE_POINTS = {"A": 3, "B": 2, "C": 1, "D": 0, "E": 0}

# ------------------------------
# Organizer dashboard + items
# ------------------------------
@login_required
def organizer_dashboard(request):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    total_items = Item.objects.count()
    total_teams = Team.objects.count()
    total_results = Result.objects.filter(is_deleted=False).count()

    context = {
        "total_items": total_items,
        "total_teams": total_teams,
        "total_results": total_results,
    }
    return render(request, "organizer/dashboard.html", context)


@login_required
def organizer_items(request):
    if request.user.role != "organizer":
        return redirect("accounts:home")

    category = request.GET.get("category", "").strip()
    q = request.GET.get("q", "").strip()

    items = (
        Item.objects.all()
        .prefetch_related("results")
        .order_by("category", "name")
    )

    if category:
        items = items.filter(category__iexact=category)

    if q:
        items = items.filter(name__icontains=q)

    # Add precomputed boolean flags to each item
    for it in items:
        it.has_results = it.results.filter(is_deleted=False).exists()
        it.team_count = it.team_set.count()

    return render(request, "organizer/items.html", {
        "items": items,
        "categories": Item.objects.values_list("category", flat=True).distinct(),
        "selected_category": category,
        "q": q,
    })


# ------------------------------
# Add results (multiple winners per position)
# ------------------------------
@login_required
def add_results(request, item_id):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    item = get_object_or_404(Item, id=item_id)
    teams = Team.objects.filter(item=item).select_related("college").prefetch_related("students")

    positions = [(1, "1st Place"), (2, "2nd Place"), (3, "3rd Place")]

    if request.method == "POST":
        # Wrap in a transaction
        with transaction.atomic():
            # soft-delete previous results for this item (keep record)
            Result.objects.filter(item=item).update(is_deleted=True)

            # For each position read posted team ids
            for pos, _label in positions:
                team_ids = request.POST.getlist(f"teams_{pos}")
                for team_id in team_ids:
                    grade = request.POST.get(f"grade_{pos}_{team_id}", "").upper().strip() or "E"
                    pos_points = POSITION_POINTS.get(pos, 0)
                    grade_points = GRADE_POINTS.get(grade, 0)
                    total_points = pos_points + grade_points

                    # create new result row
                    r = Result.objects.create(
                        item=item,
                        team_id=team_id,
                        position=pos,
                        grade=grade,
                        points=total_points,
                        is_deleted=False,
                    )
        messages.success(request, f"Results saved for item: {item.name}")
        return redirect("organizer_items")

    return render(request, "organizer/add_results.html", {
        "item": item,
        "teams": teams,
        "positions": positions,
    })


# ------------------------------
# View results for an item
# ------------------------------
@login_required
def view_results(request, item_id):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    item = get_object_or_404(Item, id=item_id)

    results = Result.objects.filter(item=item, is_deleted=False) \
        .select_related("team__college").prefetch_related("team__students") \
        .order_by("position", "-points")

    positions = [(1, "1st Place"), (2, "2nd Place"), (3, "3rd Place")]

    return render(request, "organizer/view_results.html", {
        "item": item,
        "results": results,
        "positions": positions,
    })


# ------------------------------
# Edit an individual result
# ------------------------------
@login_required
def edit_result(request, result_id):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    result = get_object_or_404(Result, id=result_id)

    if request.method == "POST":
        try:
            pos = int(request.POST.get("position"))
            grade = request.POST.get("grade", "").strip().upper()
            if pos not in (1, 2, 3):
                raise ValueError("Invalid position")
            if grade not in GRADE_POINTS:
                raise ValueError("Invalid grade")

            result.position = pos
            result.grade = grade
            result.points = POSITION_POINTS.get(pos, 0) + GRADE_POINTS.get(grade, 0)
            result.save()
            messages.success(request, "Result updated.")
            return redirect("view_results", item_id=result.item.id)
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect("edit_result", result_id=result.id)

    return render(request, "organizer/edit_result.html", {
        "result": result,
        "position_choices": [(1, "1st"), (2, "2nd"), (3, "3rd")],
        "grade_choices": ["A", "B", "C", "D", "E"],
    })


# ------------------------------
# Delete / Undo delete at item level (soft delete)
# ------------------------------
@login_required
def delete_item_results(request, item_id):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    Result.objects.filter(item_id=item_id).update(is_deleted=True)
    messages.success(request, "All results for the item have been deleted (you can undo).")
    return redirect("organizer_items")


@login_required
def undo_delete_results(request, item_id):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    Result.objects.filter(item_id=item_id).update(is_deleted=False)
    messages.success(request, "Results restored.")
    return redirect("view_results", item_id=item_id)


# ------------------------------
# Live college ranking JSON
# ------------------------------
@login_required
def college_ranking_live(request):
    if getattr(request.user, "role", None) != "organizer":
        return JsonResponse({"error": "forbidden"}, status=403)

    rankings = (
        Result.objects.filter(is_deleted=False)
        .values("team__college__id", "team__college__college_name")
        .annotate(total_points=Sum("points"))
        .order_by("-total_points", "team__college__college_name")
    )

    data = {
        "rankings": [
            {"college_id": r["team__college__id"],
             "college": r["team__college__college_name"],
             "total_points": r["total_points"] or 0}
            for r in rankings
        ]
    }
    return JsonResponse(data)


# ------------------------------
# Export PDF / Excel
# ------------------------------
# PDF using reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

@login_required
def export_results_pdf(request):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="results.pdf"'

    doc = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()
    elements = []

    results = Result.objects.filter(is_deleted=False).select_related("item", "team__college").order_by("item__category", "item__name")

    for r in results:
        text = f"{r.item.category} / {r.item.name} — {r.team.college.college_name} — {r.get_position_display()} — Grade {r.grade} — {r.points} pts"
        elements.append(Paragraph(text, styles["Normal"]))
        elements.append(Spacer(1, 6))

    doc.build(elements)
    return response


# Excel using openpyxl (optional import)
try:
    import openpyxl
    from openpyxl.workbook import Workbook
    OPENPYXL_AVAILABLE = True
except Exception:
    OPENPYXL_AVAILABLE = False


@login_required
def export_results_excel(request):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    if not OPENPYXL_AVAILABLE:
        messages.error(request, "Excel export requires openpyxl (pip install openpyxl).")
        return redirect("organizer_items")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["Category", "Item", "College", "Position", "Grade", "Points"])

    results = Result.objects.filter(is_deleted=False).select_related("item", "team__college")
    for r in results:
        ws.append([r.item.category, r.item.name, r.team.college.college_name, r.get_position_display(), r.grade, r.points])

    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="results.xlsx"'
    wb.save(response)
    return response


# ------------------------------
# Student results search
# ------------------------------
@login_required
def organizer_student_results(request):
    if getattr(request.user, "role", None) != "organizer":
        messages.error(request, "Access denied.")
        return redirect("home")

    query = request.GET.get("q", "").strip()
    student_id = request.GET.get("student_id", "").strip()

    students = []
    selected_student = None
    results = []

    if query:
        students = Student.objects.filter(name__icontains=query).select_related("college")

    if student_id:
        selected_student = get_object_or_404(Student, id=student_id)
        results = Result.objects.filter(team__students=selected_student, is_deleted=False) \
            .select_related("item", "team__college").order_by("item__category", "item__name", "position")

    return render(request, "organizer/student_results.html", {
        "query": query,
        "students": students,
        "selected_student": selected_student,
        "results": results,
    })
