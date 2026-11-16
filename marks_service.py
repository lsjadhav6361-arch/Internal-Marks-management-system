from decimal import Decimal, ROUND_HALF_UP


def round2(value):
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def calculate_converted(obtained, maximum, convert_to):
    if obtained in (None, ""):
        return 0.0
    if maximum in (None, 0, 0.0, "0", "0.0"):
        return 0.0
    return round2((float(obtained) / float(maximum)) * float(convert_to))


def parse_float(value):
    if value is None or str(value).strip() == "":
        return 0.0
    return float(value)


def validate_mark(label, value, max_value):
    if value is None or str(value).strip() == "":
        return f"{label} is required."
    try:
        val = float(value)
    except ValueError:
        return f"{label} must be numeric."
    if val < 0:
        return f"{label} cannot be negative."
    if max_value is not None and val > float(max_value):
        return f"{label} marks cannot exceed {max_value}"
    return None


def build_student_mark_payload(student, form, settings):
    usn = student["reg_no"]
    assignment = str(form.get(f"assignment_{usn}", "")).strip()
    ia1 = str(form.get(f"ia1_{usn}", "")).strip()
    ia2 = str(form.get(f"ia2_{usn}", "")).strip()
    practical_enabled = int(settings.get("practical_enabled") or 0) == 1
    practical = str(form.get(f"practical_{usn}", "")).strip() if practical_enabled else "0"
    assignment_convert_to = settings.get("assignment_convert_to")
    practical_convert_to = settings.get("practical_convert_to")

    errors = []
    for label, value, limit in [
        ("Assignment", assignment, settings["assignment_max"]),
        ("IA1", ia1, settings["ia1_max"]),
        ("IA2", ia2, settings["ia2_max"]),
        ("Practical", practical, settings["practical_max"] if practical_enabled else None),
    ]:
        err = validate_mark(label, value, limit)
        if err:
            errors.append(f"{usn}: {err}")

    if errors:
        return None, errors

    assignment_f = parse_float(assignment)
    ia1_f = parse_float(ia1)
    ia2_f = parse_float(ia2)
    practical_f = parse_float(practical)

    assignment_effective = calculate_converted(assignment_f, settings["assignment_max"], assignment_convert_to) if assignment_convert_to not in (None, "") else assignment_f
    practical_effective = calculate_converted(practical_f, settings["practical_max"], practical_convert_to) if practical_convert_to not in (None, "") else practical_f
    ia1_converted = calculate_converted(ia1_f, settings["ia1_max"], settings["ia1_convert_to"])
    ia2_converted = calculate_converted(ia2_f, settings["ia2_max"], settings["ia2_convert_to"])
    grand_total = round2(assignment_effective + ia1_converted + ia2_converted + practical_effective)

    payload = {
        "student_id": student["id"],
        "reg_no": usn,
        "student_name": student["student_name"],
        "section": student.get("section", ""),
        "assignment_marks": assignment_f,
        "ia1_marks": ia1_f,
        "ia2_marks": ia2_f,
        "practical_marks": practical_f,
        "ia1_converted": ia1_converted,
        "ia2_converted": ia2_converted,
        "grand_total": grand_total,
    }
    return payload, []
