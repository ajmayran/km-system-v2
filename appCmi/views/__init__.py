from .home_view import home, get_input_from_search  # ✅ Import the home function
from .cmi_about_view import cmi_about  # ✅ Import the about function
from .cmi_forum_view import (
    cmi_forum,
    forum_post_question,
    display_forum,
    forum_add_comment,
    toggle_forum_like,
    toggle_forum_bookmark,
)  # ✅ Import the forum function
from .cmi_commodities_view import (
    all_commodities,
    display_commodity,
)  # ✅ Import the commodities function
from .cmi_message_view import message, send_message
from .cmi_user_profile_view import (
    display_cmi_profile,
    upload_profile_picture,
    update_user_info,
)
from .cmi_knowledge_resources_view import (
    cmi_knowledge_resources,
    record_resource_view,
    toggle_bookmark,
)
from .cmi_display_post_view import cmi_display_post
from .cmi_faqs_view import (
    faqs_view,
    add_faq,
    edit_faq,
    delete_faq,
    toggle_faq_status,
    toggle_faq_reaction,
    get_faq_data,
)

from .project_view import project_detail, project_view, project_sub_view
from .project_sub_view import project_sub_detail