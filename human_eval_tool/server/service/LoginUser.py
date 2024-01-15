# -*- coding: utf-8 -*-
"""
LoginUser Class for User Authentication and Role Management

This module handles provides methods for user registration, login verification, role assignment, access control settings,
and retrieval of user and task-related information from the database. It handles the communication between our webserver
the MongoDB database server, thereby also includes functionality to update user roles and access control settings.

Author: Xiaobin Wang and Songbo Hu
Date: 20 November 2023
License: MIT License
"""

import logging

from dao.Role import Role, user_role, admin_role
from dao.User import User
from datetime import datetime
from init import pymongo, bcrypt
from bson import ObjectId

from service.TaskEnvironment import TaskEnvironment

class LoginUser:

    def __init__(self, username=None, email=None, password=None, country=None):
        """
        Initialize a User object with optional parameters.

        Args:
            username (str): The username of the user.
            email (str): The email of the user.
            password (str): The password of the user.
            country (str): The country of the user.
        """
        self.email = email
        self.password = password
        self.id = None
        self.name = username
        self.country = country
        self.task_env = TaskEnvironment()
        self.role = user_role

    def register_new_user(self):
        """
        Registers a new user.

        This function generates a password hash using bcrypt for the provided password. It then checks if the user's email is the same as the admin email set in the task environment. If it is, the user role is set to "admin_role"; otherwise, it is set to "user_role". 

        A new User object is created with the provided username, password hash, email, country, current date and time, and user role. The User object is then inserted into the "user" collection in the MongoDB database. The inserted document's ID is assigned to the "id" attribute of the calling object. Finally, the function returns the string representation of the inserted document's ID and the user role.

        Parameters:
        - None

        Returns:
        - str: The inserted document's ID.
        - str: The user role.
        """
        self.password = bcrypt.generate_password_hash(self.password).decode('utf-8')

        _this_user_role = user_role
        if self.email == self.task_env.admin_email:
            _this_user_role = admin_role

        Unew = User(username=self.name, password=self.password,
                    email=self.email, country=self.country, date_added=datetime.now(), role= _this_user_role.model_dump())
        insert_result = pymongo.db['user'].insert_one(Unew.model_dump())
        self.id = insert_result.inserted_id
        return str(self.id), _this_user_role

    def check_user_with_email(self, email):
        """
        Check if a user with the given email exists in the database.

        Args:
            email (str): The email address of the user.

        Returns:
            User or None: If a user with the given email exists, return the User object. Otherwise, return None.

        Raises:
            Exception: If there is an error in getting the MongoDB connection.

        """
        try:
            user = pymongo.db['user'].find_one({'email': email})
            if user:
                self.email = user['email']
                self.country = user['country']
                self.id = user['_id']
                self.name = user['username']
                self.password = user['password']
                self.role = Role(**user['role'])
                return self
            else:
                return None
        except Exception as e:
            logging.error('Can not get the mongodb connection', exc_info=True)
            return None

    def check_user_with_id(self, id):
        """
        Retrieves a user from the database based on their ID.

        Args:
            id (str or ObjectId): The ID of the user to retrieve.

        Returns:
            User or None: The user object if found, None otherwise.
        """
        try:
            if isinstance(id, str):
                id = ObjectId(id)

            user = pymongo.db['user'].find_one({'_id': id})
            if user:
                self.email = user['email']
                self.country = user['country']
                self.id = user['_id']
                self.name = user['username']
                self.password = user['password']
                self.role = Role(**user['role'])
                return self
            else:
                return None
        except Exception as e:
            logging.error('Failed to retrieve user from MongoDB', exc_info=True)
            return None


    def check_password(self, password):
        """
        Check if the provided password matches the user's stored password.

        Parameters:
            password (str): The password to be checked.

        Returns:
            bool: True if the password matches, False otherwise.
        """
        return bcrypt.check_password_hash(self.password, password)

    def get_task(self):
        """
        Get the task from the task environment.

        Returns:
            The task obtained from the task environment.
        """
        task = self.task_env.get_task()
        return task


    def save_result(self, feedback):
        """
        Save the given feedback result to the 'result' collection in the database.

        Parameters:
            feedback (object): The feedback object containing the model dump.

        Returns:
            str: The ID of the inserted document in the 'result' collection.
        """
        insert_result = pymongo.db['result'].insert_one(feedback.model_dump())
        insert_id = insert_result.inserted_id
        return str(insert_id)


    def assign_role(self, role: Role):
        """
        Assigns a role to the user.

        Args:
            role (Role): The role to be assigned to the user.

        Returns:
            None
        """
        self.role = role
        pymongo.db['user'].update_one({'_id': self.id}, {'$set': {'role': role.model_dump()}})

    def has_permission(self, permission: str) -> bool:
        """
        Check if the user has a specific permission.

        Parameters:
            permission (str): The permission to check.

        Returns:
            bool: True if the user has the permission, False otherwise.
        """
        print(self.role)
        if self.role:
            return permission in self.role.permissions
        return False


    def get_all_users(self):
        """
        Retrieves all users from the database and returns a list of user data.

        Returns:
            list: A list of dictionaries containing user data.
                Each dictionary contains the following keys:
                    - id (str): The unique identifier of the user.
                    - email (str): The email address of the user.
                    - name (str): The username of the user.
                    - country (str): The country of the user.
                    - role (str): The role of the user, represented as a string.
        
        Raises:
            Exception: If there is an error fetching users from the database.
        """
        try:
            users = pymongo.db['user'].find({})
            user_list = []
            for user in users:
                user_data = {
                    'id': str(user['_id']),
                    'email': user['email'],
                    'name': user['username'],
                    'country': user['country'],
                    'role': Role(**user['role']).name  # assuming Role has a 'name' attribute
                }
                user_list.append(user_data)
            return user_list
        except Exception as e:
            logging.error('Error fetching users from database', exc_info=True)
            return []

    def get_all_results(self):
        """
        Retrieve all entries from the 'result' MongoDB collection.

        :return: A list of dictionary objects representing the entries in the 'result' collection.
        """
        try:
            collection = pymongo.db['result']
            entries = collection.find({})
            formatted_results = []

            for entry in entries:
                # Convert all ObjectIds to strings
                formatted_entry = {k: str(v) if isinstance(v, ObjectId) else v for k, v in entry.items()}
                formatted_results.append(formatted_entry)

            return formatted_results
        except Exception as e:
            logging.error('Error fetching data from result collection', exc_info=True)
            return []

    def update_user_roles(self, authorised_user_ids, authorised_user_role, default_user_role):
        """Update the roles of users: set authorised_user_role for specified users, and default_user_role for others, excluding admin users."""
        try:
            # Convert string IDs to ObjectId
            authorised_user_ids = [ObjectId(user_id) if isinstance(user_id, str) else user_id for user_id in authorised_user_ids]

            # Define the admin role exclusion query
            exclude_admin_role_query = {"role.name": {"$ne": "admin"}}

            # Update users in the list to authorised_user_role, excluding admin users
            pymongo.db['user'].update_many(
                {'_id': {'$in': authorised_user_ids}, **exclude_admin_role_query},
                {'$set': {'role': authorised_user_role.model_dump()}}
            )

            # Update users not in the list to default_user_role, excluding admin users
            pymongo.db['user'].update_many(
                {'_id': {'$nin': authorised_user_ids}, **exclude_admin_role_query},
                {'$set': {'role': default_user_role.model_dump()}}
            )
        except Exception as e:
            logging.error('Error updating user roles', exc_info=True)


    def update_access_control_setting(self, enabled):
        """
        Update the access control enabled setting in the database.

        Args:
            enabled (bool): The new value for the access control setting.

        Returns:
            None

        Raises:
            Exception: If there is an error updating the access control setting.
        """
        try:
            # Connect to the database and update the access control setting
            pymongo.db['settings'].update_one(
                {'setting': 'access_control'},
                {'$set': {'enabled': enabled}},
                upsert=True
            )
        except Exception as e:
            # Log the error if there is an exception
            logging.error('Error updating access control setting', exc_info=True)

    def get_access_control_setting(self):
        """
        Retrieve the access control enabled setting from the database.

        Returns:
            bool: The value of the access control enabled setting. Defaults to False if the setting is not found.
        """
        try:
            # Find the access control setting in the database
            setting = pymongo.db['settings'].find_one({'setting': 'access_control'})
            
            # Check if the setting is found and 'enabled' key exists
            if setting and 'enabled' in setting:
                return setting['enabled']
            
            # Default to False if the setting is not found
            return False
        except Exception as e:
            # Log the error and return False
            logging.error('Error fetching access control setting', exc_info=True)
            return False
