from .dashboard_url import urlpatterns as dashboard_urlpatterns
from .users_url import urlpatterns as users_urlpatterns
from .display_map_url import urlpatterns as display_map_urlpatterns
from .commodities_url import urlpatterns as commodities_urlpatterns
from .forum_url import urlpatterns as forum_urlpatterns
from .cmi_url import urlpatterns as cmi_urlpatterns
from .knowledge_resources_url import urlpatterns as knowledge_resources_urlpatterns

urlpatterns = (
    dashboard_urlpatterns
    + users_urlpatterns
    + display_map_urlpatterns
    + forum_urlpatterns
    + commodities_urlpatterns
    + cmi_urlpatterns
    + knowledge_resources_urlpatterns
)
