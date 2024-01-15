# -*- coding: utf-8 -*-
"""
User Model for User Management

This module defines the 'User' class, a Pydantic BaseModel, for representing and managing user data in applications.
The 'User' class is designed to store essential user information and associated roles within the system,
contributing to both user management and access control functionalities.

The class includes attributes such as username, email, password, country, date_added, and role.
The role attribute links to the 'Role' class, enabling the association of users with specific roles and permissions in the system.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License

Example Usage:
The following JSON structure demonstrates how to instantiate the User class:

{
  "username": "Songbo",
  "email": "sh2091@cam.ac.uk",
  "password": "$2b$12$EguPPC3ANL6dSYztN/8ZBe2iyEaC6NvAdZuhdx/GpQSyXhfq4VqKK",
  "country": "United Kingdom",
  "date_added": {
    "$date": "2023-11-29T14:33:58.319Z"
  },
  "role": {
    "name": "admin",
    "permissions": [
      "visit_admin_page",
      "visit_task_page",
      "visit_task_page_with_access_control",
      "set_up_access_control",
      "download_data",
      "submit_task",
      "submit_task_with_access_control"
    ]
  }
},

"""

from datetime import datetime
from pydantic import BaseModel
from dao.Role import Role


class User(BaseModel):
    """
    A Pydantic model for representing users in an application.

    Attributes:
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The hased password for the user's account.
        country (str): The country of residence of the user.
        date_added (datetime): The date and time when the user was added to the system.
        role (Role): The role assigned to the user, with associated permissions.
    """

    username: str
    email: str
    password: str
    country: str
    date_added: datetime
    role: Role = None

    def __repr__(self):
        role_repr = self.role.__repr__() if self.role else "None"
        return (f'User(email="{self.email}", username="{self.username}",'
                f'password="{self.password}", country="{self.country}", role={role_repr})')

