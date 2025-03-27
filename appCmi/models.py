from django.db import models
from django.utils import timezone
from utils.slug_generator import generate_random_slug


class Forum(models.Model):
    forum_id = models.AutoField(primary_key=True)
    forum_title = models.CharField(max_length=255, db_collation="utf8mb4_unicode_ci")
    forum_question = models.TextField()
    commodity_id = models.ManyToManyField(
        "appAdmin.Commodity", related_name="forum_tag_commodity"
    )
    author = models.ForeignKey("appAccounts.CustomUser", on_delete=models.CASCADE)
    bookmark = models.ManyToManyField(
        "appAccounts.CustomUser", blank=True, related_name="user_bookmarked_forum"
    )
    slug = models.CharField(
        max_length=12, unique=True, default=generate_random_slug, editable=False
    )
    date_posted = models.DateField(default=timezone.now, null=True)

    class Meta:
        db_table = "tbl_forum"


class FilteredCommodityFrequency(models.Model):
    filter_id = models.AutoField(primary_key=True)
    commodity = models.ForeignKey("appAdmin.Commodity", on_delete=models.CASCADE)
    frequency = models.IntegerField(default=1)
    date_filtered = models.DateField(default=timezone.now)

    class Meta:
        db_table = "tbl_commodity_filtered"

    def update_or_create_frequency(self, commodity):
        """
        Optimized method to update frequency for today's date.
        If an entry exists, increment frequency; otherwise, create a new entry.
        """
        today_date = timezone.now().date()

        # Optimized: Use update_or_create to reduce database queries
        obj, created = FilteredCommodityFrequency.objects.update_or_create(
            commodity=commodity,
            date_filtered=today_date,
            defaults={"frequency": models.F("frequency") + 1} if not created else {},
        )
