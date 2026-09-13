"""
Context processor to inject session-based user info into templates.
This bridges the gap between session-based auth and template rendering.
"""

def auth_context(request):
    """
    Add authentication context from session to all templates.
    Provides: is_authenticated, user_id, role, email, full_name
    """
    user_id = request.session.get("user_id")
    
    return {
        "is_authenticated": bool(user_id),
        "user_id": user_id,
        "user_role": request.session.get("role"),
        "user_email": request.session.get("email"),
        "user_full_name": request.session.get("full_name"),
    }
