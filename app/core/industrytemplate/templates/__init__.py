"""Sektörel agent şablon tanımları.

E-ticaret, medikal turizm, gayrimenkul,
dijital ajans hazır şablonları.
"""

from app.core.industrytemplate.templates.ecommerce import ECOMMERCE_TEMPLATE
from app.core.industrytemplate.templates.medical_tourism import MEDICAL_TOURISM_TEMPLATE
from app.core.industrytemplate.templates.real_estate import REAL_ESTATE_TEMPLATE
from app.core.industrytemplate.templates.digital_agency import DIGITAL_AGENCY_TEMPLATE

__all__ = [
    "ECOMMERCE_TEMPLATE",
    "MEDICAL_TOURISM_TEMPLATE",
    "REAL_ESTATE_TEMPLATE",
    "DIGITAL_AGENCY_TEMPLATE",
]
