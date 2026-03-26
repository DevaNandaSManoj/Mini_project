from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from datetime import date, timedelta
from django.utils.dateparse import parse_date
import calendar
from sklearn.linear_model import LinearRegression
import numpy as np
import json

from food.models import StudentDailyRecord, DailyMenu
from accounts.models import Student


@login_required
def mess_dashboard(request):
    if request.user.role != 'mess':
        return redirect('login')

    today = date.today()
    tomorrow = today + timedelta(days=1)

    # ── TODAY ──────────────────────────────────────────
    today_records = StudentDailyRecord.objects.filter(date=today)

    breakfast_count  = today_records.filter(breakfast=True).count()
    lunch_count      = today_records.filter(lunch=True).count()
    dinner_count     = today_records.filter(dinner=True).count()
    total_meals_today = breakfast_count + lunch_count + dinner_count

    # Students who opted for at least one meal today
    students_opted = today_records.filter(
        Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
    ).values('student').distinct().count()

    total_students  = Student.objects.count()
    skipped_students = total_students - students_opted

    # ── TOMORROW ───────────────────────────────────────
    tomorrow_records = StudentDailyRecord.objects.filter(date=tomorrow)
    tomorrow_bookings = tomorrow_records.filter(
        Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
    ).values('student').distinct().count()

    # ── WEEKLY SNAPSHOT (last 7 days including today) ──
    week_start = today - timedelta(days=6)
    weekly_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_records = StudentDailyRecord.objects.filter(date=day)
        opted = day_records.filter(
            Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
        ).values('student').distinct().count()
        weekly_data.append({'date': day, 'opted': opted})

    opted_counts   = [d['opted'] for d in weekly_data]
    avg_participation = round(sum(opted_counts) / len(opted_counts), 1) if opted_counts else 0

    highest_day_data = max(weekly_data, key=lambda x: x['opted']) if weekly_data else None
    lowest_day_data  = min(weekly_data, key=lambda x: x['opted']) if weekly_data else None

    # ── TODAY'S MENU ───────────────────────────────────
    try:
        today_menu = DailyMenu.objects.get(date=today)
    except DailyMenu.DoesNotExist:
        today_menu = None

    # ── ALERTS ─────────────────────────────────────────
    alerts = []
    if skipped_students > total_students * 0.5:
        alerts.append({
            'type': 'warning',
            'icon': 'fa-triangle-exclamation',
            'message': f'More than half of students ({skipped_students}) have not opted for any meal today.',
        })
    try:
        tomorrow_menu_dash = DailyMenu.objects.get(date=tomorrow)
    except DailyMenu.DoesNotExist:
        tomorrow_menu_dash = None

    if tomorrow_menu_dash is None or (
        not tomorrow_menu_dash.breakfast and
        not tomorrow_menu_dash.lunch and
        not tomorrow_menu_dash.dinner
    ):
        alerts.append({
            'type': 'danger',
            'icon': 'fa-circle-exclamation',
            'message': "Tomorrow's menu has not been set yet.",
        })
    if tomorrow_bookings == 0:
        alerts.append({
            'type': 'info',
            'icon': 'fa-circle-info',
            'message': 'No students have booked meals for tomorrow yet.',
        })

    # Max for progress bars
    max_meal = max(breakfast_count, lunch_count, dinner_count, 1)

    context = {
        # Today
        'today': today,
        'breakfast_count': breakfast_count,
        'lunch_count': lunch_count,
        'dinner_count': dinner_count,
        'total_meals_today': total_meals_today,
        'students_opted': students_opted,
        'skipped_students': skipped_students,
        'total_students': total_students,
        'max_meal': max_meal,

        # Tomorrow
        'tomorrow': tomorrow,
        'tomorrow_bookings': tomorrow_bookings,

        # Weekly
        'weekly_data': weekly_data,
        'avg_participation': avg_participation,
        'highest_day': highest_day_data,
        'lowest_day': lowest_day_data,

        # Menu
        'today_menu': today_menu,   # actually tomorrow's menu for display

        # Alerts
        'alerts': alerts,
    }

    return render(request, 'mess_manager/dashboard.html', context)


@login_required
def edit_menu(request):
    if request.user.role != 'mess':
        return redirect('login')

    today = date.today()
    tomorrow = today + timedelta(days=1)

    # ── LOAD / CREATE TOMORROW'S MENU ─────────────────────────────────────────
    tomorrow_menu, _ = DailyMenu.objects.get_or_create(
        date=tomorrow,
        defaults={'breakfast': '', 'lunch': '', 'dinner': ''},
    )

    if request.method == 'POST':
        tomorrow_menu.breakfast = request.POST.get('breakfast', '').strip()
        tomorrow_menu.lunch = request.POST.get('lunch', '').strip()
        tomorrow_menu.dinner = request.POST.get('dinner', '').strip()
        tomorrow_menu.save()
        messages.success(request, "Tomorrow's menu updated successfully!")
        return redirect('edit_menu')

    # ── LAST 7 DAYS DATA (for analytics) ─────────────────────────────────────
    days_7 = [today - timedelta(days=i) for i in range(6, -1, -1)]  # oldest→newest

    breakfast_counts = []
    lunch_counts = []
    dinner_counts = []

    for d in days_7:
        recs = StudentDailyRecord.objects.filter(date=d)
        breakfast_counts.append(recs.filter(breakfast=True).count())
        lunch_counts.append(recs.filter(lunch=True).count())
        dinner_counts.append(recs.filter(dinner=True).count())

    # ── AI SUGGESTIONS (most-selected item in last 7 days) ────────────────────
    suggestion_breakfast = _most_selected_menu_item(days_7, 'breakfast')
    suggestion_lunch = _most_selected_menu_item(days_7, 'lunch')
    suggestion_dinner = _most_selected_menu_item(days_7, 'dinner')

    # ── ML PREDICTIONS (LinearRegression) ────────────────────────────────────
    X = np.array([[1], [2], [3], [4], [5], [6], [7]])

    predicted_breakfast = _ml_predict(X, breakfast_counts)
    predicted_lunch = _ml_predict(X, lunch_counts)
    predicted_dinner = _ml_predict(X, dinner_counts)

    # ── DEMAND TREND (last 3 days vs prior 3 days) ─────────────────────────────
    def _trend(counts):
        recent = sum(counts[-3:])
        earlier = sum(counts[:3])
        if recent > earlier:
            return 'Increasing'
        elif recent < earlier:
            return 'Decreasing'
        return 'Stable'

    trend_breakfast = _trend(breakfast_counts)
    trend_lunch = _trend(lunch_counts)
    trend_dinner = _trend(dinner_counts)

    # ── ALERTS ────────────────────────────────────────────────────────────────
    total_students = Student.objects.count()
    # Tomorrow's bookings so far
    tomorrow_records = StudentDailyRecord.objects.filter(date=tomorrow)
    students_opted_tomorrow = tomorrow_records.filter(
        Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
    ).values('student').distinct().count()

    alerts = []
    if total_students > 0 and students_opted_tomorrow < total_students * 0.3:
        alerts.append({
            'type': 'warning',
            'icon': 'fa-triangle-exclamation',
            'message': f'Low bookings for tomorrow — only {students_opted_tomorrow} of {total_students} students have selected meals.',
        })
    if not tomorrow_menu.breakfast and not tomorrow_menu.lunch and not tomorrow_menu.dinner:
        alerts.append({
            'type': 'info',
            'icon': 'fa-circle-info',
            'message': "Tomorrow's menu is empty. Please fill in the menu details below.",
        })

    context = {
        'today': today,
        'tomorrow': tomorrow,
        'tomorrow_menu': tomorrow_menu,
        # AI suggestions
        'suggestion_breakfast': suggestion_breakfast,
        'suggestion_lunch': suggestion_lunch,
        'suggestion_dinner': suggestion_dinner,
        # ML predictions
        'predicted_breakfast': predicted_breakfast,
        'predicted_lunch': predicted_lunch,
        'predicted_dinner': predicted_dinner,
        # Trends
        'trend_breakfast': trend_breakfast,
        'trend_lunch': trend_lunch,
        'trend_dinner': trend_dinner,
        # Alerts
        'alerts': alerts,
        # Stats
        'total_students': total_students,
        'students_opted_tomorrow': students_opted_tomorrow,
    }
    return render(request, 'mess_manager/edit_menu.html', context)


# ── STATISTICS ──────────────────────────────────────────────────────────────

@login_required
def meal_statistics(request):
    if request.user.role != 'mess':
        return redirect('login')

    today = date.today()
    total_students = Student.objects.count()

    # ── 1. TODAY ──────────────────────────────────────────────────────────────
    today_records = StudentDailyRecord.objects.filter(date=today)
    breakfast_count = today_records.filter(breakfast=True).count()
    lunch_count     = today_records.filter(lunch=True).count()
    dinner_count    = today_records.filter(dinner=True).count()

    # ── 2. WEEKLY (last 7 days) ───────────────────────────────────────────────
    week_labels = []
    week_participation = []   # % of students per day
    week_opted_counts  = []   # raw opted counts

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        recs = StudentDailyRecord.objects.filter(date=day)
        opted = recs.filter(
            Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
        ).values('student').distinct().count()
        pct = round((opted / total_students * 100), 1) if total_students > 0 else 0
        week_labels.append(day.strftime('%a %d'))
        week_participation.append(pct)
        week_opted_counts.append(opted)

    avg_participation = round(sum(week_participation) / len(week_participation), 1)
    peak_idx = week_participation.index(max(week_participation))
    low_idx  = week_participation.index(min(week_participation))
    peak_day_label   = week_labels[peak_idx]
    lowest_day_label = week_labels[low_idx]
    peak_pct         = week_participation[peak_idx]
    lowest_pct       = week_participation[low_idx]

    # Trend: last 3 vs first 3 days
    recent3 = sum(week_participation[-3:])
    older3  = sum(week_participation[:3])
    if recent3 > older3:
        trend = 'Increasing'
        trend_icon = 'fa-arrow-trend-up'
        trend_color = '#34d399'
    elif recent3 < older3:
        trend = 'Decreasing'
        trend_icon = 'fa-arrow-trend-down'
        trend_color = '#f87171'
    else:
        trend = 'Stable'
        trend_icon = 'fa-minus'
        trend_color = '#fbbf24'

    # ── 3. MONTHLY (last 6 months) ────────────────────────────────────────────
    month_labels = []
    month_totals  = []
    for m in range(5, -1, -1):
        # Go back m months from current month
        yr = today.year
        mo = today.month - m
        while mo <= 0:
            mo += 12
            yr -= 1
        month_start = date(yr, mo, 1)
        _, last_day = calendar.monthrange(yr, mo)
        month_end = date(yr, mo, last_day)
        recs = StudentDailyRecord.objects.filter(date__gte=month_start, date__lte=month_end)
        total = (recs.filter(breakfast=True).count() +
                 recs.filter(lunch=True).count() +
                 recs.filter(dinner=True).count())
        month_labels.append(month_start.strftime('%b'))
        month_totals.append(total)

    # ── 4. WASTE ESTIMATION (last 3 months, bi-monthly buckets) ─────────────────
    # Each month is split into two halves: 1st–14th and 15th–end
    waste_labels = []
    waste_counts = []
    for m in range(2, -1, -1):
        yr = today.year
        mo = today.month - m
        while mo <= 0:
            mo += 12
            yr -= 1
        _, last_day = calendar.monthrange(yr, mo)
        # Half 1: 1st → 14th
        h1_start = date(yr, mo, 1)
        h1_end   = date(yr, mo, 14)
        # Half 2: 15th → end
        h2_start = date(yr, mo, 15)
        h2_end   = date(yr, mo, last_day)

        for (hstart, hend, label_day) in [(h1_start, h1_end, 1), (h2_start, h2_end, 15)]:
            skip_total = 0
            current = hstart
            while current <= hend and current <= today:
                day_recs = StudentDailyRecord.objects.filter(date=current)
                opted = day_recs.filter(
                    Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
                ).values('student').distinct().count()
                skip_total += max(total_students - opted, 0)
                current += timedelta(days=1)
            waste_labels.append(f"{date(yr, mo, label_day).strftime('%b')} {label_day}")
            waste_counts.append(skip_total)

    total_waste_week = sum(waste_counts)
    waste_trend = 'High' if total_waste_week > total_students * 3 else 'Moderate' if total_waste_week > total_students else 'Low'
    waste_color = '#f87171' if waste_trend == 'High' else '#fbbf24' if waste_trend == 'Moderate' else '#34d399'

    # ── 5. SMART INSIGHTS ────────────────────────────────────────────────────
    # Already computed: peak_day_label, lowest_day_label, avg_participation, trend

    # ── 6. ML PREDICTIONS ────────────────────────────────────────────────────
    X_7 = np.array([[1],[2],[3],[4],[5],[6],[7]])
    X_6 = np.array([[1],[2],[3],[4],[5],[6]])

    # A) Participation prediction (based on last 7 days)
    y_part = np.array(week_participation, dtype=float)
    model_part = LinearRegression()
    model_part.fit(X_7, y_part)
    predicted_participation = max(0, round(float(model_part.predict([[8]])[0]), 1))
    predicted_participation = min(predicted_participation, 100.0)

    # B) Waste prediction (based on last 6 bi-monthly buckets)
    y_waste = np.array(waste_counts, dtype=float)
    model_waste = LinearRegression()
    model_waste.fit(X_6, y_waste)
    predicted_waste = max(0, round(float(model_waste.predict([[7]])[0])))

    # ── ALERTS ────────────────────────────────────────────────────────────────
    alerts = []
    today_opted = today_records.filter(
        Q(breakfast=True) | Q(lunch=True) | Q(dinner=True)
    ).values('student').distinct().count()
    today_skipped = max(total_students - today_opted, 0)
    if total_students > 0 and today_skipped > total_students * 0.5:
        alerts.append({
            'type': 'warning',
            'icon': 'fa-triangle-exclamation',
            'message': f'High skip rate today — {today_skipped} of {total_students} students skipped all meals.',
        })
    if waste_trend == 'High':
        alerts.append({
            'type': 'danger',
            'icon': 'fa-trash-can',
            'message': f'High waste this week ({total_waste_week} estimated skipped portions). Consider portion adjustments.',
        })
    if avg_participation < 40:
        alerts.append({
            'type': 'danger',
            'icon': 'fa-circle-exclamation',
            'message': f'Low weekly participation average ({avg_participation}%). Investigate student meal preferences.',
        })
    if trend == 'Decreasing':
        alerts.append({
            'type': 'warning',
            'icon': 'fa-arrow-trend-down',
            'message': 'Participation is trending downward over the last 7 days.',
        })
    if predicted_participation > avg_participation + 10:
        alerts.append({
            'type': 'info',
            'icon': 'fa-circle-info',
            'message': f'AI predicts higher participation tomorrow ({predicted_participation}%). Plan accordingly.',
        })

    context = {
        'today': today,
        'total_students': total_students,
        # Today
        'breakfast_count': breakfast_count,
        'lunch_count': lunch_count,
        'dinner_count': dinner_count,
        # Weekly
        'week_labels_json': json.dumps(week_labels),
        'week_participation_json': json.dumps(week_participation),
        'week_opted_counts_json': json.dumps(week_opted_counts),
        'avg_participation': avg_participation,
        'peak_day_label': peak_day_label,
        'peak_pct': peak_pct,
        'lowest_day_label': lowest_day_label,
        'lowest_pct': lowest_pct,
        'trend': trend,
        'trend_icon': trend_icon,
        'trend_color': trend_color,
        # Monthly
        'month_labels_json': json.dumps(month_labels),
        'month_totals_json': json.dumps(month_totals),
        # Waste
        'waste_labels_json': json.dumps(waste_labels),
        'waste_counts_json': json.dumps(waste_counts),
        'total_waste_week': total_waste_week,
        'waste_trend': waste_trend,
        'waste_color': waste_color,
        # ML Predictions
        'predicted_participation': predicted_participation,
        'predicted_waste': predicted_waste,
        # Alerts
        'alerts': alerts,
    }
    return render(request, 'mess_manager/statistics.html', context)


# ── HELPERS ───────────────────────────────────────────────────────────────────

@login_required
def mess_meal_analysis(request):
    if request.user.role != 'mess':
        return redirect('login')

    selected_date_str = request.GET.get('date')
    selected_month_str = request.GET.get('month')

    records = StudentDailyRecord.objects.all()

    # Filter by date or month
    if selected_date_str:
        records = records.filter(date=parse_date(selected_date_str))
        period_text = "Based on selected date"
    elif selected_month_str:
        try:
            year, month = map(int, selected_month_str.split('-'))
            records = records.filter(date__year=year, date__month=month)
            period_text = f"Based on {selected_month_str} average"
        except ValueError:
            period_text = "Based on all time"
    else:
        # Default to last 30 days if no filter
        thirty_days_ago = date.today() - timedelta(days=30)
        records = records.filter(date__gte=thirty_days_ago)
        period_text = "Based on last 30 days average"

    # Aggregate data
    student_meal_counts = records.aggregate(
        b_count=Count('id', filter=Q(breakfast=True)),
        l_count=Count('id', filter=Q(lunch=True)),
        d_count=Count('id', filter=Q(dinner=True))
    )

    b_count = student_meal_counts['b_count'] or 0
    l_count = student_meal_counts['l_count'] or 0
    d_count = student_meal_counts['d_count'] or 0

    counts = {
        'Breakfast': b_count,
        'Lunch': l_count,
        'Dinner': d_count
    }

    total_recs = records.count()

    # Find most selected and most skipped
    min_count = min(counts.values())
    max_count = max(counts.values())

    if min_count == max_count:
        if max_count == 0:
            most_selected_meal = "No Data"
            most_skipped_meal = "No Data"
        else:
            most_selected_meal = "All Equal"
            most_skipped_meal = "None (All Equal)"
    else:
        max_meals = [k for k, v in counts.items() if v == max_count]
        most_selected_meal = " & ".join(max_meals)

        min_meals = [k for k, v in counts.items() if v == min_count]
        most_skipped_meal = " & ".join(min_meals)

    most_selected_count = max_count
    most_skipped_count = total_recs - min_count

    context = {
        "selected_date_str": selected_date_str or '',
        "selected_month_str": selected_month_str or '',
        "period_text": period_text,
        "breakfast_count": b_count,
        "lunch_count": l_count,
        "dinner_count": d_count,
        "breakfast_skip": total_recs - b_count,
        "lunch_skip": total_recs - l_count,
        "dinner_skip": total_recs - d_count,
        "most_selected_meal": most_selected_meal,
        "most_selected_count": most_selected_count,
        "most_skipped_meal": most_skipped_meal,
        "most_skipped_count": most_skipped_count,
    }

    return render(request, 'mess_manager/meal_analysis.html', context)



def _most_selected_menu_item(days_7, meal_field):
    """Return the menu item name most frequently chosen by students over last 7 days."""
    from django.db.models import Count as _Count
    counts = {}
    for d in days_7:
        opted = StudentDailyRecord.objects.filter(
            date=d, **{meal_field: True}
        ).count()
        try:
            menu = DailyMenu.objects.get(date=d)
            item_name = getattr(menu, meal_field, '').strip()
        except DailyMenu.DoesNotExist:
            item_name = ''
        if item_name:
            counts[item_name] = counts.get(item_name, 0) + opted
    if not counts:
        return 'No data'
    return max(counts, key=counts.get)


def _ml_predict(X, counts):
    """Train a LinearRegression model on the 7-day counts and predict day 8."""
    y = np.array(counts, dtype=float)
    # If all zeros sklearn can still fit — no special case needed
    model = LinearRegression()
    model.fit(X, y)
    prediction = model.predict([[8]])[0]
    return max(0, round(prediction))  # can't have negative students
