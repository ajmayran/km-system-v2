from django.shortcuts import render, get_object_or_404
from appCmi.models import Forum, ForumComment, FilteredCommodityFrequency
from appAdmin.models import Commodity
from django.db.models import Count, Sum
from django.utils import timezone
from utils.user_control import user_access_required


@user_access_required("admin")
def manage_forum(request):
    """Dashboard for admin forum management"""

    # Get main statistics
    total_discussions = Forum.objects.count()
    active_discussions = (
        Forum.objects.annotate(comment_count=Count("post_comments"))
        .filter(
            comment_count__gt=0,
            date_posted__gte=timezone.now() - timezone.timedelta(days=30),
        )
        .count()
    )

    total_comments = ForumComment.objects.count()
    total_reactions = (
        Forum.objects.annotate(like_count=Count("likes")).aggregate(
            total_likes=Sum("like_count")
        )["total_likes"]
        or 0
    )

    # Get all discussions with related author and commodity
    all_discussions = (
        Forum.objects.select_related("author")
        .prefetch_related("commodity_id")  # Use the field name, NOT the related name
        .annotate(comment_count=Count("post_comments"))
    )

    # Get top commodities
    top_commodities = Commodity.objects.annotate(
        forum_count=Count("forum_tag_commodity")
    ).order_by("-forum_count")[:5]

    # Search terms analysis (from FilteredCommodityFrequency)
    search_terms = FilteredCommodityFrequency.objects.select_related(
        "commodity"
    ).order_by("-frequency")[:10]

    # Get recent comments
    recent_comments = ForumComment.objects.select_related("user", "post")

    # Context dictionary
    context = {
        "total_discussions": total_discussions,
        "active_discussions": active_discussions,
        "total_comments": total_comments,
        "total_reactions": total_reactions,
        "all_discussions": all_discussions,  # Now contains all forum discussions
        "top_commodities": top_commodities,
        "search_terms": search_terms,
        "recent_comments": recent_comments,
    }

    return render(request, "pages/admin-forum.html", context)


@user_access_required("admin")
def get_comments_per_forum_post(request, slug):
    """Get comments for a specific forum post"""
    forum_post = get_object_or_404(Forum, slug=slug)
    comments = ForumComment.objects.filter(post=forum_post)
    return render(request, "pages/admin-forum.html", {"comments": comments})
