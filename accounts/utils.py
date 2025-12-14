def calculate_points(position, grade):
    position_points = {1: 5, 2: 3, 3: 1}
    grade_points = {"A": 3, "B": 2, "C": 1, "D": 0, "E": 0}
    return position_points.get(position, 0) + grade_points.get(grade, 0)
