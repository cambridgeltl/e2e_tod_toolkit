# -*- coding: utf-8 -*-
"""
Authentication and User Management

This script defines a Flask RESTFUL APIs that handle user authentication, registration, logout, and various user-related
tasks within this evaluation tool. It uses JWT (JSON Web Tokens) for secure and stateless authentication. The APIs provide
endpoints for login, registration, logout, task retrieval, result submission, user management, and access control configuration.

Author: Xiaobin Wang and Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import create_access_token, unset_jwt_cookies, get_jwt_identity
from flask_cors import CORS
from dao.FeedBack import FeedBack
from dao.Role import authorised_user_role, user_role
from service.LoginUser import LoginUser
from flask_jwt_extended import jwt_required
from view.decorators import require_permission, require_additional_permission_with_access_control

auth = Blueprint('auth', __name__)

CORS(auth, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

@auth.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Handles user login requests.

    This API authenticates users by their email and password. If authentication is successful, it generates and returns a JWT access token.

    Returns:
        Response: A JSON response containing the authentication status and, on successful authentication, a JWT access token.
    """
    if request.method == 'OPTIONS':
        return _handle_preflight()

    data = request.data
    if data:
        _datadetail = json.loads(data)
        _email = _datadetail['email']
        _password_in = _datadetail['password']
        _lo_user = LoginUser()
        _lo_user = _lo_user.check_user_with_email(_email)
        if not _lo_user:
            res = jsonify({'success': False, 'msg': 'This user does not exist'})
            return res

        if _lo_user.check_password(_password_in):
            access_token = create_access_token(identity=str(_lo_user.id),
                                               additional_claims={"role": _lo_user.role.model_dump()})
            response = jsonify({'success': True, 'access_token': access_token, 'msg': 'login successfully'})

            return response
        else:
            res = jsonify({'success': False, 'msg': 'Wrong password'})
            return res


@auth.route("/register", methods=["POST", 'OPTIONS'])
def register():
    """
    Handles new user registration requests.

    This API registers a new user with the provided username, email, password, and country. It checks for existing users
    with the same email to avoid duplicates. On successful registration, it returns a JWT access token for immediate login.

    Returns:
        Response: A JSON response containing the registration status and, on successful registration, a JWT access token.
    """

    if request.method == 'OPTIONS':
        return _handle_preflight()
    registerdata = request.data
    registerdata = json.loads(registerdata)
    if registerdata:
        _user_name = registerdata['username']
        _email = registerdata['email']
        _password = registerdata['password']
        _country = registerdata['country']
        _newUser = LoginUser(username=_user_name, email=_email, password=_password, country=_country)
        user_exists = _newUser.check_user_with_email(_email)

        if user_exists:
            response = jsonify({'success': False, 'msg': 'register user has existed'})
            return response
        try:
            _userid, _user_role = _newUser.register_new_user()
            access_token = create_access_token(identity=str(_userid),
                                               additional_claims={"role": _user_role.model_dump()})

            response = jsonify(
                {'success': True, 'access_token': access_token, 'msg': 'register and login successfully'})

            return response

        except Exception as e:
            logging.error('Register failed', exc_info=True)
            response = jsonify({'success': False, 'msg': 'register failed'})
            return response

    return jsonify({'success': False, 'msg': 'register failed, no data fund'}), 400


@auth.route("/logout", methods=['POST', 'OPTION'])
def logout():
    """
    Handles user logout requests.

    TODO：Modify this function if it is necessary in the future. Currently, not in use.

    Returns:
        Response: A JSON response indicating successful logout.
    """

    response = jsonify({"msg": "logout successful"})
    return response


@auth.route("/get_task", methods=['GET'])
@jwt_required()
@require_permission('visit_task_page')
def get_task():
    """
    Retrieves a task for the logged-in user.

    This API fetches a task for a user with the required permissions. It requires JWT authentication and specific permissions to access.

    Returns:
        Response: A JSON response with the task details on success, or an error message on failure.
    """

    current_user_id = get_jwt_identity()

    try:
        _currentUser = LoginUser().check_user_with_id(current_user_id)

        _currentTask = _currentUser.get_task()

        return jsonify({'success': True, 'msg': 'Get task success.', 'task': _currentTask}), 200

    except Exception as e:
        logging.error('Error while fetching user data', exc_info=True)
        return jsonify({'success': False, 'msg': 'Failed to fetch task data'}), 500


@auth.route("/save_result", methods=['POST', "OPTIONS"])
@jwt_required()
@require_permission('submit_task')
@require_additional_permission_with_access_control("submit_task_with_access_control")
def save_result():
    """
    Handles the submission of task results by the user.

    This API endpoint allows authenticated users to submit their task results. It requires JWT authentication and specific permissions.

    Returns:
        Response: A JSON response indicating the success or failure of the save operation.
    """

    if request.method == 'OPTIONS':
        return _handle_preflight()
    current_user_id = get_jwt_identity()

    try:
        _currentUser = LoginUser().check_user_with_id(current_user_id)
        save_data = request.get_json()
        logging.info(save_data)
        if save_data:
            save_data['create_time'] = datetime.now()
            save_data['feedback_user'] = _currentUser.email
            _feedback = FeedBack(**save_data)
            insert_id = _currentUser.save_result(_feedback)

            return jsonify({'success': True, 'msg': 'Save success.', "insert_id": insert_id}), 200

    except Exception as e:
        logging.error('Error while saving task data', exc_info=True)
        return jsonify({'success': False, 'msg': 'Failed to save task data'}), 500


@auth.route("/get_all_users", methods=['GET'])
@jwt_required()
@require_permission('visit_admin_page')
def get_all_users():
    """
    Retrieves a list of all users in the system.

    This endpoint is typically used by administrators to fetch details of all users. It requires JWT authentication and admin-level permissions.

    Returns:
        Response: A JSON response with a list of all users and their details, or an error message on failure.
    """

    current_user_id = get_jwt_identity()

    try:
        _currentUser = LoginUser().check_user_with_id(current_user_id)
        _currentUserList = _currentUser.get_all_users()
        _access_control_enabled = _currentUser.get_access_control_setting()

        return jsonify({
            'success': True,
            'msg': 'Get user list success.',
            'user_list': _currentUserList,
            'access_control_enabled': _access_control_enabled
        }), 200

    except Exception as e:
        logging.error('Error while fetching user data', exc_info=True)
        return jsonify({'success': False, 'msg': 'Failed to fetch all user data'}), 500


@auth.route("/submit_access_control", methods=['POST', "OPTIONS"])
@jwt_required()
@require_permission('visit_admin_page')
def submit_access_control():
    """
    Update of access control settings.

    This endpoint allows administrators to update access control settings, including the list of authorized users and the status of access control.
    It requires JWT authentication and admin-level permissions.

    Returns:
        Response: A JSON response indicating the success or failure of the update operation.
    """

    if request.method == 'OPTIONS':
        return _handle_preflight()

    current_user_id = get_jwt_identity()
    try:
        _currentUser = LoginUser().check_user_with_id(current_user_id)

        data = request.get_json()

        allowed_list = data.get('allowed_list', [])
        enabled = data.get('has_access_control', False)

        _currentUser = LoginUser()
        _currentUser.update_user_roles(allowed_list, authorised_user_role, user_role)
        _currentUser.update_access_control_setting(enabled)

        return jsonify({'success': True, 'msg': 'Save success.'}), 200

    except Exception as e:
        logging.error('Error while saving role data', exc_info=True)
        return jsonify({'success': False, 'msg': 'Failed to save task data'}), 500


@auth.route("/get_access_control", methods=['GET'])
@jwt_required()
@require_permission('visit_task_page')
def get_access_control():
    """
    Retrieves the current access control settings.

    This endpoint provides the status of access control settings, such as whether it is enabled and the list of users with special access.
    It requires JWT authentication and specific permissions.

    Returns:
        Response: A JSON response with access control settings, or an error message on failure.
    """

    current_user_id = get_jwt_identity()

    try:
        _currentUser = LoginUser().check_user_with_id(current_user_id)
        _access_control_enabled = _currentUser.get_access_control_setting()

        return jsonify({
            'success': True,
            'msg': 'Get access control status success.',
            'access_control_enabled': _access_control_enabled
        }), 200

    except Exception as e:
        logging.error('Error while fetching access control status', exc_info=True)
        return jsonify({'success': False, 'msg': 'Failed to fetch access control status'}), 500



@auth.route("/get_all_results", methods=['GET'])
@jwt_required()
@require_permission('visit_admin_page')  # Assuming only admins should access this
def get_all_results_api():
    """
    Retrieves all task results stored in the system.

    This endpoint is designed for administrators to fetch the results of all tasks submitted by users. It requires JWT authentication and admin-level permissions.

    Returns:
        Response: A JSON response containing all task results, or an error message on failure.
    """

    current_user_id = get_jwt_identity()

    try:
        _currentUser = LoginUser().check_user_with_id(current_user_id)
        results = _currentUser.get_all_results()
        formatted_results = [result for result in results]
        return jsonify({'success': True, 'data': formatted_results}), 200
    except Exception as e:
        logging.error('Error while fetching results', exc_info=True)
        return jsonify({'success': False, 'msg': 'Failed to fetch results'}), 500

def _handle_preflight():
    """
    Handles preflight requests for CORS.

    This function is called for OPTIONS requests to any of the routes. It sets the necessary headers for CORS support.
    Sometimes, we need this to support the Safari Browser in a development environment.

    Returns:
        Response: A Flask response object with CORS headers set.
    """

    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response