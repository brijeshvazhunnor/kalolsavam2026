from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import LoginForm, RegisterForm, StudentForm, ItemForm, RegistrationForm
from .models import Student, Item, Registration, College, Team


# ---------------- Homepage ----------------
def home(request):
    return render(request, 'accounts/home.html')


from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

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
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


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
from django.contrib.auth import logout
from django.shortcuts import redirect

def user_logout(request):
    logout(request)
    request.session.flush()  # 🔥 VERY IMPORTANT
    return redirect("login")



# ---------------- College Dashboard ----------------
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

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






@login_required
def admin_dashboard(request):
    if request.user.role != "admin":
        return redirect("home")
    return render(request, "admin/dashboard.html")



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
