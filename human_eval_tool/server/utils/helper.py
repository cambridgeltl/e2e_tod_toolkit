# -*- coding: utf-8 -*-
"""
Secure Password Hashing Utility

This script provides a utility function for securely hashing passwords using the bcrypt hashing algorithm.

Author: Xiaobin Wang
Date: 20 November 2023
License: MIT License
"""

import bcrypt


def hash_password(password):
    """
        Generate a hashed password using bcrypt.

        Args:
            password (str): The password to be hashed.

        Returns:
            str: The hashed password.
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())