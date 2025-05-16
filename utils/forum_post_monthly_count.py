def get_forum_posts_by_month_current_year():
    """
    Returns the total count of forum posts grouped by month for the current year.

    Returns:
        dict: A dictionary containing months data, total posts, and percentage change
    """
    from appCmi.models import Forum
    from django.utils import timezone
    from datetime import datetime
    from collections import Counter

    # Get current year
    current_year = datetime.now().year

    # Get all forum posts for the current year
    forums = Forum.objects.filter(
        date_posted__year=current_year, date_posted__isnull=False
    )

    # Use Counter to count posts by month
    month_counts = Counter()
    for forum in forums:
        month = forum.date_posted.month
        month_counts[month] += 1

    # Map of month numbers to month names (full names for display)
    month_names = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    # Map of month numbers to abbreviated names (for chart labels)
    month_abbr = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }

    # Initialize data for all months (even those with zero posts)
    processed_data = []
    monthly_totals = []
    formatted_months = []  # For display in format "January: 10"

    # For debugging - print the raw counts from Counter
    print("Month counts from Counter:")
    for month_num in range(1, 13):
        count = month_counts[month_num]
        print(f"Month {month_num}: {count} posts")

    # Process data for all months
    total_posts = 0
    for month_num in range(1, 13):
        post_count = month_counts[month_num]
        total_posts += post_count

        month_data = {
            "month_num": month_num,
            "month_name": month_abbr[month_num],
            "full_month_name": month_names[month_num],
            "total": post_count,
        }
        processed_data.append(month_data)
        monthly_totals.append(post_count)
        formatted_months.append(f"{month_names[month_num]}: {post_count}")

    # Calculate average posts per month
    avg_posts = total_posts / 12 if total_posts > 0 else 0

    # Calculate percentage changes for display
    # For the total percentage change, compare current month with previous month
    current_month = timezone.now().month
    previous_month = current_month - 1 if current_month > 1 else 12

    current_month_posts = month_counts[current_month]
    previous_month_posts = month_counts[previous_month]

    # Calculate percentage change (avoid division by zero)
    if previous_month_posts > 0:
        total_percentage_change = (
            (current_month_posts - previous_month_posts) / previous_month_posts
        ) * 100
    else:
        total_percentage_change = 100 if current_month_posts > 0 else 0

    # Calculate percentage difference from average
    if avg_posts > 0:
        avg_percentage_diff = ((current_month_posts - avg_posts) / avg_posts) * 100
    else:
        avg_percentage_diff = 100 if current_month_posts > 0 else 0

    # Determine if trends are up or down
    total_trend = "up" if total_percentage_change >= 0 else "down"
    avg_trend = "up" if avg_percentage_diff >= 0 else "down"

    return {
        "months_data": processed_data,
        "monthly_totals": monthly_totals,
        "formatted_months": formatted_months,
        "total_posts": total_posts,
        "avg_posts": round(avg_posts, 1),
        "total_percentage": abs(round(total_percentage_change)),
        "avg_percentage": abs(round(avg_percentage_diff)),
        "total_trend": total_trend,
        "avg_trend": avg_trend,
    }
