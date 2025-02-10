#!/usr/bin/python3
from datetime import date
from typing import List

from pydantic import Field

from mssdk.core.models.mapping_package import MappingPackageEligibilityConstraints


# eforms_package.py
# Date:  10/02/2025
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com


class eFormsEligibilityConstraints(MappingPackageEligibilityConstraints):
    """A class representing eligibility constraints specific to eForms mapping packages.

    This class defines the conditions and constraints that determine when and how
    an eForms mapping package can be applied. It includes version compatibility,
    applicable subtypes, and temporal validity constraints for eForms documents.

    The constraints ensure that mapping packages are only applied to compatible
    eForms documents within their intended scope and validity period.

    """

    eForms_subtype: List[str] = Field(...,
                                      description="List of eForms subtypes (e.g., CN, PIN) that this mapping package supports")
    eForms_version: List[str] = Field(...,
                                      description="List of eForms SDK versions (e.g., 1.0.0, 1.1.0) that are compatible with this mapping package")
    start_date: date = Field(...,
                             description="ISO formatted date (YYYY-MM-DD) indicating when this mapping package becomes valid for use")
    end_date: date = Field(...,
                           description="ISO formatted date (YYYY-MM-DD) indicating when this mapping package expires")
