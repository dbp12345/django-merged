from functools import wraps
from django.shortcuts import redirect

def employee_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.session.get("employee_id"):
            return redirect("pwa_crwb_login")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
