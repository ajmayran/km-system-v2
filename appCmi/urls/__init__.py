from .home_url import (
    urlpatterns as home_url_urlpatterns,
)
from .cmi_about_url import (
    urlpatterns as cmi_about_url_urlpatterns,
)
from .cmi_forum_url import (
    urlpatterns as forum_url_urlpatterns,
)
from .cmi_commodities_url import (
    urlpatterns as commodities_url_urlpatterns,
)
from .cmi_message_url import (
    urlpatterns as message_url_urlpatterns,
)
from .cmi_user_profile_url import (
    urlpatterns as user_profile_url_urlpatterns,
)
from .cmi_knowledge_resources_url import (
    urlpatterns as knowledge_resources_url_urlpatterns,
)
from .cmi_display_post_url import (
    urlpatterns as display_post_url_urlpatterns,
)

urlpatterns = (
    home_url_urlpatterns
    + cmi_about_url_urlpatterns
    + forum_url_urlpatterns
    + commodities_url_urlpatterns
    + message_url_urlpatterns
    + user_profile_url_urlpatterns
    + knowledge_resources_url_urlpatterns
    + display_post_url_urlpatterns
)
