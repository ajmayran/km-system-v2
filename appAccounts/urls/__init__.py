from .login_url import urlpatterns as login_patterns
from .registration_url import urlpatterns as registration_patterns
from .account_activation_url import urlpatterns as account_activation_patterns
from .logout_url import urlpatterns as logout_patterns
from .password_reset_url import urlpatterns as password_reset_patterns
from .enter_email_url import urlpatterns as enter_email_patterns
from .request_new_activation_code_url import (
    urlpatterns as request_new_activation_code_patterns,
)
from .cmi_change_pass_url import urlpatterns as cmi_change_pass_patterns

from appAccounts.views import *

# Merge the urlpatterns from both files
urlpatterns = (
    login_patterns
    + registration_patterns
    + account_activation_patterns
    + logout_patterns
    + password_reset_patterns
    + enter_email_patterns
    + request_new_activation_code_patterns
    + cmi_change_pass_patterns
)
