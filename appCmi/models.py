from django.db import models
from django.utils import timezone


class Forum(models.Model):
    forum_id = models.AutoField(primary_key=True)
    forum_title = models.CharField(max_length=255)
    forum_question = models.TextField()
    commodity_id = models.ManyToManyField(
        "appAdmin.Commodity", related_name="forum_tag_commodity"
    )
    author = models.ForeignKey("appAccounts.CustomUser", on_delete=models.CASCADE)
    bookmark = models.ManyToManyField(
        "appAccounts.CustomUser", blank=True, related_name="user_bookmarked_forum"
    )
    date_posted = models.DateField(default=timezone.now, null=True)

    class Meta:
        db_table = "tbl_forum"
