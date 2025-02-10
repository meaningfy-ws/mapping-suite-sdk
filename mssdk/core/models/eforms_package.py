#!/usr/bin/python3

# eforms_package.py
# Date:  10/02/2025
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """
from mssdk.core.models.mapping_package import MappingPackageEligibilityConstraints


class eFormsEligibilityConstraints(MappingPackageEligibilityConstraints):
    eForms_subtype: list[str]
    eForms_version: list[str]
    start_date: str
    end_date: str
