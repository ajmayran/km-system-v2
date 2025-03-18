from .dashboard_url import urlpatterns as dashboard_urlpatterns
from .users_url import urlpatterns as users_urlpatterns
from .display_map_url import urlpatterns as display_map_urlpatterns
from .commodities_url import urlpatterns as commodities_urlpatterns
from .forum_url import urlpatterns as forum_urlpatterns

urlpatterns = (
    dashboard_urlpatterns
    + users_urlpatterns
    + display_map_urlpatterns
    + forum_urlpatterns
    + commodities_urlpatterns
)
