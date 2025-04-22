from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
import random
import string
from django.utils.text import slugify

# ACCOUNTS


class CustomUserManager(BaseUserManager):
    def _create_user(self, email, password=None, **extra_fields):
        """Private method to handle user creation logic."""
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)

        # Check if a user with the same email exists
        if self.model.objects.filter(email=email).exists():
            raise ValueError("A user with this email already exists")

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Creates a default user with the role of CMI."""
        extra_fields.setdefault("user_type", CustomUser.CMI)
        return self._create_user(email, password, **extra_fields)

    def create_secretariat(self, email, password=None, **extra_fields):
        """Creates a user with the Secretariat role."""
        extra_fields.setdefault("user_type", CustomUser.SECRETARIAT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Creates a superuser (admin only)."""
        extra_fields.setdefault("user_type", CustomUser.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self._create_user(email, password, **extra_fields)


def generate_random_slug():
    return "".join(random.choices(string.ascii_letters + string.digits, k=12))


class CustomUser(AbstractUser):
    """Custom User model with additional fields and email-based authentication."""

    SECRETARIAT = "secretariat"
    CMI = "cmi"
    ADMIN = "admin"

    USER_TYPES = [
        (SECRETARIAT, "Secretariat"),
        (CMI, "CMI"),
        (ADMIN, "Admin User"),
    ]

    middle_name = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField(max_length=255, unique=True, blank=False)
    institution = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    date_birth = models.DateField(null=True, blank=True)  # Date of birth
    sex = models.CharField(max_length=20, null=True, blank=True)  # Sex of the user
    gender = models.CharField(max_length=20, null=True, blank=True)  # Gender identity
    specialization = models.CharField(
        max_length=255, null=True, blank=True
    )  # Specialization
    highest_educ = models.CharField(
        max_length=255, null=True, blank=True
    )  # Education level
    contact_num = models.CharField(
        max_length=15, null=True, blank=True
    )  # Contact number
    user_type = models.CharField(
        max_length=20, choices=USER_TYPES, null=True, blank=True
    )
    date_created = models.DateField(default=timezone.now, null=True, blank=True)

    # Unique random slug
    slug = models.CharField(
        max_length=12, unique=True, default=generate_random_slug, editable=False
    )

    # Override default username handling
    username = models.CharField(max_length=150, unique=True, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        """Ensure username is None if left blank and ensure a unique slug."""
        if self.username == "":
            self.username = None

        # Ensure slug is unique when creating a new instance
        if not self.slug:
            while True:
                new_slug = generate_random_slug()
                if not CustomUser.objects.filter(slug=new_slug).exists():
                    self.slug = new_slug
                    break

        super().save(*args, **kwargs)

    def generate_unique_username(self):
        """Generates a unique username based on email."""
        base_username = slugify(self.email.split("@")[0])
        unique_username = base_username
        num = 1
        while CustomUser.objects.filter(username=unique_username).exists():
            unique_username = f"{base_username}{num}"
            num += 1
        return unique_username


class Profile(models.Model):
    """User Profile model linked to the CustomUser model."""

    profile_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    picture = models.ImageField(upload_to="user-profiles/", null=True, blank=True)

    class Meta:
        db_table = "tbl_profile_pictures"
