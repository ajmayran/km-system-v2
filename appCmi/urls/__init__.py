from .home_url import (
    urlpatterns as home_url_urlpatterns,
)
from .cmi_about_url import (
    urlpatterns as cmi_about_url_urlpatterns,
)
from .forum_url import (
    urlpatterns as forum_url_urlpatterns,
)

urlpatterns = home_url_urlpatterns + cmi_about_url_urlpatterns + forum_url_urlpatterns
