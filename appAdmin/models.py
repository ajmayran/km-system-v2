from django.db import models
from django.utils import timezone
from utils.slug_generator import generate_random_slug
from embed_video.fields import EmbedVideoField


class Commodity(models.Model):
    commodity_id = models.AutoField(primary_key=True)
    slug = models.CharField(
        max_length=12, unique=True, default=generate_random_slug, editable=False
    )
    commodity_name = models.CharField(max_length=100)
    description = models.TextField()
    resources_type = models.CharField(max_length=100)
    commodity_img = models.ImageField(upload_to="commodities/", null=True)
    date_created = models.DateTimeField(default=timezone.now, null=True)
    date_edited = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=255, default="active")
    latitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:  # Ensure the slug is only set once
            self.slug = generate_random_slug()
        if self.pk:
            self.date_edited = timezone.now().date()
        super(Commodity, self).save(*args, **kwargs)

    def __str__(self):
        return self.commodity_name

    class Meta:
        db_table = "tbl_commodity"


class KnowledgeResources(models.Model):
    knowledge_id = models.AutoField(primary_key=True)
    slug = models.CharField(
        max_length=12, unique=True, default=generate_random_slug, editable=False
    )
    knowledge_title = models.CharField(max_length=255)
    knowledge_description = models.TextField()
    status = models.CharField(max_length=255, default="active")
    date_created = models.DateTimeField(default=timezone.now, null=True)

    class Meta:
        db_table = "tbl_knowledge_resources"


class About(models.Model):
    about_id = models.AutoField(primary_key=True)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "tbl_about"


class AboutFooter(models.Model):
    about_footer_id = models.AutoField(primary_key=True)
    content_footer = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "tbl_about_footer"


class CMI(models.Model):
    cmi_id = models.AutoField(primary_key=True)
    slug = models.CharField(
        max_length=12, unique=True, default=generate_random_slug, editable=False
    )
    cmi_name = models.CharField(max_length=255)  # acronym
    cmi_meaning = models.CharField(max_length=255)  # meaning of the cmi name acronym
    cmi_description = models.TextField()
    address = models.CharField(max_length=255, null=True)
    contact_num = models.CharField(max_length=20, null=True)
    email = models.EmailField(null=True)
    cmi_image = models.ImageField(upload_to="cmi/", null=True)
    status = models.CharField(max_length=255, default="active")
    latitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )
    url = models.URLField(null=True)
    date_joined = models.DateField(null=True)
    date_created = models.DateField(default=timezone.now)

    class Meta:
        db_table = "tbl_cmi"


class UsefulLinks(models.Model):
    link_id = models.AutoField(primary_key=True)
    link_title = models.CharField(max_length=255, null=True)
    link = models.URLField(null=True, blank=True)
    status = models.CharField(max_length=255, default="active")
    date_created = models.DateField(auto_now_add=True, null=True)

    class Meta:
        db_table = "tbl_useful_links"


class UploadVideo(models.Model):
    video_id = models.AutoField(primary_key=True)
    video_title = models.CharField(max_length=255)
    url = EmbedVideoField()

    class Meta:
        db_table = "tbl_about_video"


# class Carousel(models.Model):
#     carousel_id = models.AutoField(primary_key=True)
#     alt = models.CharField(max_length=255, null=True)
#     img_path = models.ImageField(upload_to="carousel/", null=True, blank=True)
#     commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, null=True)

#     class Meta:
#         db_table = "tbl_carousel"

# class Events(models.Model):
#     event_id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=255, null=True, blank=True)
#     start = models.DateField(null=True, blank=True)
#     end = models.DateField(null=True, blank=True)

#     class Meta:
#         db_table = "tbl_events"
