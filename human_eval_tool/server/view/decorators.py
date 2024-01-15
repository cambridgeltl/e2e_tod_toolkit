# -*- coding: utf-8 -*-
"""
Flask Access Control Utilities

This script defines utilities for handling access control. It includes decorators for permission-based access control.

The `require_permission` decorator ensures that the current user has the specified permission before allowing access to a route.
The `require_additional_permission_with_access_control` decorator adds an extra layer of access control based on system-wide settings.

Author: Songbo Hu and Xiaobin Wang
Date: 20 November 2023
License: MIT License

"""
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from service.LoginUser import LoginUser


def require_permission(permission):
    """
    Decorator to require a specific permission for accessing a route.

    This decorator checks if the current authenticated user has the specified permission. If the user does not have the required permission, it returns a 403 Forbidden response.

    Args:
        permission (str): The required permission for the route.

    Returns:
        Function: A decorated route function that includes permission checking.
    """

    def decorator(f):
        @wraps(f)
        @jwt_required()  # Ensure JWT token is verified
        def decorated_function(*args, **kwargs):
            if request.method == 'OPTIONS':
                return f(*args, **kwargs)
            # Assuming you have some way of getting the current user
            current_user = get_current_user()  # Implement this function as needed
            # current_user.get_access_control_setting()
            if not current_user or not current_user.has_permission(permission):
                return jsonify({'message': 'Permission denied'}), 403

            print("require_permission pass")
            return f(*args, **kwargs)

        return decorated_function

    return decorator



def require_additional_permission_with_access_control(permission):
    """
    Decorator to require a specific permission for a route when access control is enabled.

    This decorator extends 'require_permission' by adding an additional layer of access control. It checks if access control is enabled and then verifies the user's permission.
    If access control is enabled and the user lacks the required permission, it returns a 403 Forbidden response.

    Args:
        permission (str): The required permission for the route.

    Returns:
        Function: A decorated route function that includes permission checking with access control.
    """

    def decorator(f):
        @wraps(f)
        @jwt_required()  # Ensure JWT token is verified
        def decorated_function(*args, **kwargs):
            if request.method == 'OPTIONS':
                return f(*args, **kwargs)
            # Assuming you have some way of getting the current user
            current_user = get_current_user()  # Implement this function as needed
            access_control_enabled = current_user.get_access_control_setting()
            if access_control_enabled:
                if not current_user or not current_user.has_permission(permission):
                    return jsonify({'message': 'Permission denied under access control setting'}), 403
            print("access_control")
            print(access_control_enabled)
            print("require_permission pass")
            return f(*args, **kwargs)

        return decorated_function

    return decorator

def get_current_user():
    """
    Retrieves the current authenticated user based on JWT token.

    This function extracts the user ID from the JWT token and retrieve
    s the corresponding user object from the database.

    Returns:
        LoginUser: The currently authenticated user object.
    """

    current_user_id = get_jwt_identity()

    _currentUser = LoginUser().check_user_with_id(current_user_id)
    return _currentUser
