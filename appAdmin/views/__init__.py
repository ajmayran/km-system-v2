from .dashboard_view import dashboard
from .users_view import display_users
from .display_map_view import (
    display_map,
    map_add_cmi_commodity,
)
from .commodities_view import (
    admin_commodities,
    admin_add_commodity,
    admin_edit_commodity,
    admin_delete_commodity,
)
from .forum_view import manage_forum, get_comments_per_forum_post
from .cmi_view import (
    admin_cmi,
    admin_add_cmi,
    admin_edit_cmi,
    admin_delete_cmi,
)
from .knowledge_resources_view import (
    admin_knowledge_resources,
    admin_add_knowledge_resource,
    admin_edit_knowledge_resource,
    admin_delete_knowledge_resource,
)
from .about_view import (
    admin_about_page,
    admin_about_footer,
    admin_about_page_edit,
    admin_about_footer_edit,
    admin_upload_video,
)

from .useful_link_view import (
    admin_useful_links,
    admin_add_useful_link,
    admin_edit_useful_link,
    admin_delete_useful_link,
)

from .resources_post_view import (
    admin_resources_post,
    admin_add_resources_post,
    admin_edit_resources_post,
    admin_delete_resources_post,
)

from .message_view import message_from_cmi
