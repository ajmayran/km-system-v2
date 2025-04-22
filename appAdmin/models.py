from django.db import models
from django.utils import timezone
from utils.slug_generator import generate_random_slug
from embed_video.fields import EmbedVideoField
from django.urls import reverse
from django.utils.text import slugify

# ADMIN


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
    machine_name = models.CharField(max_length=255, blank=True)  # New field
    status = models.CharField(max_length=255, default="active")
    date_created = models.DateTimeField(default=timezone.now, null=True)

    class Meta:
        db_table = "tbl_knowledge_resources"

    def save(self, *args, **kwargs):
        # Generate machine_name from title if not provided
        if not self.machine_name:
            self.machine_name = slugify(self.knowledge_title).replace("-", "_")
        super().save(*args, **kwargs)


class ResourceMetadata(models.Model):
    RESOURCE_TYPES = [
        ("event", "Events"),
        ("info_system", "Information Systems/Websites"),
        ("map", "Maps"),
        ("media", "Media"),
        ("news", "News"),
        ("policy", "Policies"),
        ("project", "Projects"),
        ("publication", "Publications"),
        ("technology", "Technologies"),
        ("training", "Training/Seminars"),
        ("webinar", "Webinars"),
        ("product", "Products"),
    ]

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "appAccounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="resources_created",
    )

    # Common fields for tagging and organization
    tags = models.ManyToManyField(
        "Tag",
        max_length=100,
        blank=True,
        db_table="tbl_knowledge_resources_metadata_tags",
    )
    commodities = models.ManyToManyField(
        Commodity,
        max_length=100,
        blank=True,
        db_table="tbl_knowledge_resources_metadata_commodities",
    )

    # Fields for controlling access/visibility
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        db_table = "tbl_knowledge_resources_metadata"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("resource_detail", kwargs={"slug": self.slug})


class Event(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="event"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    organizer = models.CharField(max_length=255)
    event_file = models.FileField(upload_to="knowledge_resources/events/")
    is_virtual = models.BooleanField(default=False)

    class Meta:
        db_table = "tbl_knowledge_resources_event"

    def __str__(self):
        return f"Event: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"slug": self.slug})


class InformationSystem(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="information_system"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    website_url = models.URLField()
    system_owner = models.CharField(max_length=255)
    last_updated = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "tbl_knowledge_resources_information_system"

    def __str__(self):
        return f"InfoSystem: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("info_system_detail", kwargs={"slug": self.slug})


class Map(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="map"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    map_file = models.FileField(upload_to="maps/")
    map_url = models.URLField(blank=True)
    latitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=11, decimal_places=8, null=True, blank=True
    )

    class Meta:
        db_table = "tbl_knowledge_resources_map"

    def __str__(self):
        return f"Map: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("map_detail", kwargs={"slug": self.slug})


class Media(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="media"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    media_type = models.CharField(
        max_length=50,
        choices=[
            ("image", "Image"),
            ("video", "Video"),
            ("audio", "Audio"),
            ("presentation", "Presentation"),
        ],
    )
    media_file = models.FileField(upload_to="knowledge_resources/media/")
    media_url = models.URLField(blank=True)
    author = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "tbl_knowledge_resources_media"

    def __str__(self):
        return f"Media: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("media_detail", kwargs={"slug": self.slug})


class News(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="news"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    publication_date = models.DateField()
    source = models.CharField(max_length=255)
    external_url = models.URLField(blank=True)
    content = models.TextField()
    featured_image = models.ImageField(
        upload_to="knowledge_resources/news_images/", blank=True, null=True
    )

    class Meta:
        db_table = "tbl_knowledge_resources_news"

    def __str__(self):
        return f"News: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("news_detail", kwargs={"slug": self.slug})


class Policy(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="policy"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    policy_number = models.CharField(max_length=100, blank=True)
    effective_date = models.DateField()
    issuing_body = models.CharField(max_length=255)
    policy_file = models.FileField(upload_to="knowledge_resources/policies/")
    policy_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("draft", "Draft"),
            ("active", "Active"),
            ("superseded", "Superseded"),
            ("archived", "Archived"),
        ],
    )

    class Meta:
        db_table = "tbl_knowledge_resources_policy"

    def __str__(self):
        return f"Policy: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("policy_detail", kwargs={"slug": self.slug})


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="project"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    funding_source = models.CharField(max_length=255, blank=True)
    project_lead = models.CharField(max_length=255)
    contact_email = models.EmailField(blank=True)
    status = models.CharField(
        max_length=50,
        choices=[
            ("ongoing", "Ongoing"),
            ("completed", "Completed"),
            ("terminated", "Terminated"),
        ],
    )

    class Meta:
        db_table = "tbl_knowledge_resources_project"

    def __str__(self):
        return f"Project: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("project_detail", kwargs={"slug": self.slug})


class Publication(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="publication"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    authors = models.CharField(max_length=500)
    publication_date = models.DateField()
    publisher = models.CharField(max_length=255, blank=True)
    doi = models.CharField(max_length=100, blank=True, verbose_name="DOI")
    isbn = models.CharField(max_length=20, blank=True, verbose_name="ISBN")
    publication_type = models.CharField(
        max_length=100,
        choices=[
            ("journal", "Journal Article"),
            ("conference", "Conference Paper"),
            ("book", "Book"),
            ("report", "Technical Report"),
            ("thesis", "Thesis/Dissertation"),
            ("other", "Other"),
        ],
    )
    publication_file = models.FileField(
        upload_to="knowledge_resources/publications/", blank=True, null=True
    )

    class Meta:
        db_table = "tbl_knowledge_resources_publication"

    def __str__(self):
        return f"Publication: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("publication_detail", kwargs={"slug": self.slug})


class Technology(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="technology"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    developer = models.CharField(max_length=255)
    release_date = models.DateField(blank=True, null=True)
    patent_number = models.CharField(max_length=100, blank=True)
    license_type = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "tbl_knowledge_resources_technology"

    def __str__(self):
        return f"Technology: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("technology_detail", kwargs={"slug": self.slug})


class TrainingSeminar(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="training_seminar"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    trainers = models.TextField(blank=True)
    target_audience = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "tbl_knowledge_resources_training_seminar"

    def __str__(self):
        return f"Training/Seminar: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("training_detail", kwargs={"slug": self.slug})


class Webinar(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="webinar"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    webinar_date = models.DateTimeField()
    duration_minutes = models.IntegerField(default=60)
    platform = models.CharField(max_length=100)
    presenters = models.TextField()

    class Meta:
        db_table = "tbl_knowledge_resources_webinar"

    def __str__(self):
        return f"Webinar: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("webinar_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    metadata = models.OneToOneField(
        ResourceMetadata, on_delete=models.CASCADE, related_name="product"
    )
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)
    manufacturer = models.CharField(max_length=255)
    features = models.TextField()
    technical_specifications = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        db_table = "tbl_knowledge_resources_product"

    def __str__(self):
        return f"Product: {self.metadata.title}"

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})


class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=255, unique=True, default=generate_random_slug)

    class Meta:
        db_table = "tbl_knowledge_resources_tag"

    def __str__(self):
        return self.name


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
