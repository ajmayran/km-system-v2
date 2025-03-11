from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import base36_to_int, int_to_base36
import six
import datetime


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk)
            + six.text_type(timestamp)
            + six.text_type(user.is_active)
        )

    def check_token(self, user, token):
        if not super().check_token(user, token):
            return False

        # Decode the token to get the timestamp
        try:
            ts_b36, _ = token.split("-")
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check if the token is older than one week
        if (self._num_seconds(self._now()) - ts) > 604800:  # 604800 seconds = 1 week
            return False

        return True

    def base36_to_int(self, s):
        return int(s, 36)


account_activation_token = AccountActivationTokenGenerator()
