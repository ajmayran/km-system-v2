from django.db.models import Count, F, Sum, Value, IntegerField, Case, When
from django.db.models.functions import Coalesce


def get_top_10_tagged_commodities():
    """
    Returns the top 10 most frequently tagged commodities across the system.

    This function aggregates commodity usage from:
    1. Forums (where commodities are tagged)
    2. Knowledge Resources (where commodities are associated with resources)
    3. FilteredCommodityFrequency (where direct commodity views/filters are tracked)

    Returns:
        QuerySet: A queryset of Commodity objects with an additional 'total_tags'
                 attribute, ordered by total_tags in descending order, limited to 10.
    """
    from appAdmin.models import Commodity
    from appCmi.models import Forum, FilteredCommodityFrequency

    # Count commodities tagged in forums
    forum_counts = (
        Forum.objects.values("commodity_id")
        .annotate(count=Count("commodity_id"))
        .values("commodity_id", "count")
    )

    # Create a dictionary to map commodity IDs to their forum counts
    forum_counts_dict = {item["commodity_id"]: item["count"] for item in forum_counts}

    # Count commodities used in knowledge resources
    resource_counts = Commodity.objects.annotate(
        resource_count=Count("resourcemetadata")
    )

    # Get the sum of frequencies from FilteredCommodityFrequency
    filter_counts = FilteredCommodityFrequency.objects.values("commodity").annotate(
        filter_count=Sum("frequency")
    )

    # Create a dictionary to map commodity IDs to their filter counts
    filter_counts_dict = {
        item["commodity"]: item["filter_count"] for item in filter_counts
    }

    # Get all commodities and annotate with total tags
    top_commodities = (
        Commodity.objects.filter(status="active")
        .annotate(
            # Count from forums (or 0 if none)
            forum_tags=Coalesce(
                Sum(
                    Case(
                        When(forum_tag_commodity__isnull=False, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
                Value(0),
            ),
            # Count from resource metadata (or 0 if none)
            resource_tags=Count("resourcemetadata", distinct=True),
            # Count from filtered frequency (or 0 if none)
            filter_tags=Coalesce(
                Sum(
                    Case(
                        When(
                            filteredcommodityfrequency__isnull=False,
                            then=F("filteredcommodityfrequency__frequency"),
                        ),
                        default=Value(0),
                        output_field=IntegerField(),
                    )
                ),
                Value(0),
            ),
        )
        .annotate(
            # Calculate the total tags
            total_tags=F("forum_tags")
            + F("resource_tags")
            + F("filter_tags")
        )
        .order_by("-total_tags")[:10]
    )

    return top_commodities
