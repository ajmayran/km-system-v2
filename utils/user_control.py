from django.shortcuts import redirect, reverse
from django.http import Http404, HttpResponseForbidden
from functools import wraps


def user_access_required(allowed_user_types=None, error_type=403):
    """
    Decorator to restrict view access based on user authentication and user_type.

    Args:
        allowed_user_types (list or str): List of allowed user types or a single user type string
                                        (e.g., 'admin', 'cmi', or ['admin', 'cmi'])
        error_type (int): Type of error to raise if access is denied (403 or 404)

    Usage:
        @user_access_required('admin')
        def admin_only_view(request):
            # Only accessible by admin users
            ...

        @user_access_required(['admin', 'cmi'], error_type=404)
        def shared_view(request):
            # Accessible by both admin and cmi users, shows 404 if denied
            ...
    """
    if isinstance(allowed_user_types, str):
        allowed_user_types = [allowed_user_types]

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return redirect("login")  # Redirect to login page if not authenticated

            # Get user_type (adjust this according to your user model structure)
            user_type = getattr(request.user, "user_type", None)

            # If no user types are specified, any authenticated user can access
            if not allowed_user_types:
                return view_func(request, *args, **kwargs)

            # Check if user has the required user_type
            if user_type in allowed_user_types:
                return view_func(request, *args, **kwargs)

            # User doesn't have access, redirect to appropriate error page
            if error_type == 404:
                return redirect(reverse("appErrors:error-404"))
            else:  # default to 403
                return redirect(reverse("appErrors:error-403"))

        return wrapper

    return decorator
