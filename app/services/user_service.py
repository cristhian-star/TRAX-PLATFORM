def is_user_active(user):
    return user is not None and user.estado == "ACTIVO"
