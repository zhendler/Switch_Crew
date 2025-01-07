"""
Password Utility Module

This module provides utility functions for handling password encryption and verification.
It uses the Passlib library with the bcrypt hashing algorithm to securely store and verify passwords.

Components:
    - `pwd_context`: A Passlib context object configured to use bcrypt hashing for password management.
    - `verify_password`: Function to verify if the plain password matches the hashed password.
    - `get_password_hash`: Function to generate a hashed version of a plain password.

Dependencies:
    - Passlib: A library for password hashing and verification.
    
Usage:
    - Use `get_password_hash` to hash a password before storing it.
    - Use `verify_password` to check if the input password matches the stored hash.
"""

from passlib.context import CryptContext


"""
CryptContext for Password Hashing

This object provides an abstraction for hashing and verifying passwords using various algorithms.
In this module, it is configured to use bcrypt as the hashing scheme and supports automatic handling of deprecated algorithms.

Attributes:
    - schemes (list): The list of hashing schemes to be used, which in this case is set to bcrypt.
    - deprecated (str): Specifies the behavior for deprecated schemes. "auto" allows automatic handling of deprecated algorithms.

Note:
    The `pwd_context` object is used to hash passwords and verify them.
"""

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    """
    Verify if the plain password matches the hashed password.

    Args:
        plain_password (str): The password input by the user in plain text.
        hashed_password (str): The hashed password stored in the database.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    """
    Hash a plain password using bcrypt.

    Args:
        password (str): The plain text password to be hashed.

    Returns:
        str: The hashed version of the password.

    Example:
        hashed_pw = get_password_hash("my_secret_password")
        print(hashed_pw)  # A bcrypt-hashed password
    """
    return pwd_context.hash(password)