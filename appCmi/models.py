from django.db import models
from django.utils import timezone
from utils.slug_generator import generate_random_slug
from django.urls import reverse


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
    date_posted = models.DateTimeField(default=timezone.now, null=True)
    likes = models.ManyToManyField(
        "appAccounts.CustomUser", related_name="liked_forums", blank=True
    )

    class Meta:
        db_table = "tbl_forum"

    def total_likes(self):
        return self.likes.count()

    def is_liked_by(self, user):
        return self.likes.filter(id=user.id).exists()

    def is_bookmarked_by(self, user):
        return self.bookmark.filter(id=user.id).exists()


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


class ForumComment(models.Model):
    STATUS_CHOICES = (
        ("active", ("Active")),
        ("hidden", ("Hidden")),
        ("deleted", ("Deleted")),
    )

    post = models.ForeignKey(
        Forum, on_delete=models.CASCADE, related_name="post_comments"
    )
    user = models.ForeignKey(
        "appAccounts.CustomUser",
        on_delete=models.CASCADE,
        related_name="post_comments_user",
    )
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    like_count = models.PositiveIntegerField(default=0)
    # Optional JSON field for additional metadata
    metadata = models.JSONField(null=True, blank=True)
    slug = models.CharField(
        max_length=12, unique=True, default=generate_random_slug, editable=False
    )

    class Meta:
        ordering = ["created_at"]
        db_table = "tbl_forum_comment"

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"

    def save(self, *args, **kwargs):
        if self.pk:
            # If comment already exists and content is changed
            orig = ForumComment.objects.get(pk=self.pk)
            if orig.content != self.content:
                self.is_edited = True
        super().save(*args, **kwargs)

    @property
    def total_likes(self):
        return self.likes.count()

    def is_liked_by(self, user):
        return self.likes.filter(user=user).exists()

    def get_absolute_url(self):
        return reverse(
            "appCmi:display-forum",
            kwargs={"forum_slug": self.post.slug, "comment_slug": self.slug},
        )
