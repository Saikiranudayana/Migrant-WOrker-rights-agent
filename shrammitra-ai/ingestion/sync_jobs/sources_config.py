"""
Official source configuration for Indian labour law documents.

All URLs point to government / authoritative portals.
No scraping of private or unofficial sites.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

SOURCE_TYPE_PDF = "pdf"
SOURCE_TYPE_WEBSITE = "website"
SOURCE_TYPE_CIRCULAR = "circular"


@dataclass
class SourceConfig:
    """A single ingestion source definition."""
    url: str
    title: str
    source_type: str          # "pdf" | "website" | "circular"
    language: str = "en"
    act_name: str = ""
    priority: int = 1          # 1 = highest; processed first


SOURCES: List[SourceConfig] = [
    # ─── Ministry of Labour & Employment ─────────────────────────────────────
    SourceConfig(
        url="https://labour.gov.in/sites/default/files/TheMinimumWagesAct1948.pdf",
        title="The Minimum Wages Act, 1948",
        source_type="pdf",
        act_name="Minimum Wages Act, 1948",
        priority=1,
    ),
    SourceConfig(
        url="https://labour.gov.in/sites/default/files/PaymentofWagesAct1936.pdf",
        title="The Payment of Wages Act, 1936",
        source_type="pdf",
        act_name="Payment of Wages Act, 1936",
        priority=1,
    ),
    SourceConfig(
        url="https://labour.gov.in/sites/default/files/TheInterStateMigrantWorkmenAct1979.pdf",
        title="Inter-State Migrant Workmen (Regulation of Employment and Conditions of Service) Act, 1979",
        source_type="pdf",
        act_name="Inter-State Migrant Workmen Act, 1979",
        priority=1,
    ),
    SourceConfig(
        url="https://labour.gov.in/sites/default/files/ContractLabourAct1970.pdf",
        title="Contract Labour (Regulation and Abolition) Act, 1970",
        source_type="pdf",
        act_name="Contract Labour Act, 1970",
        priority=1,
    ),
    SourceConfig(
        url="https://labour.gov.in/sites/default/files/BuildingOtherConstructionWorkersAct1996.pdf",
        title="Building and Other Construction Workers Act, 1996",
        source_type="pdf",
        act_name="Building and Other Construction Workers Act, 1996",
        priority=1,
    ),
    SourceConfig(
        url="https://labour.gov.in/sites/default/files/FactoriesAct1948.pdf",
        title="The Factories Act, 1948",
        source_type="pdf",
        act_name="Factories Act, 1948",
        priority=2,
    ),
    SourceConfig(
        url="https://labour.gov.in/sites/default/files/MaternityBenefitAmendmentAct2017.pdf",
        title="Maternity Benefit (Amendment) Act, 2017",
        source_type="pdf",
        act_name="Maternity Benefit Act, 1961",
        priority=2,
    ),

    # ─── EPFO (Employee Provident Fund) ──────────────────────────────────────
    SourceConfig(
        url="https://www.epfindia.gov.in/site_docs/PDFs/Downloads_PDFs/EPFAct1952.pdf",
        title="Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
        source_type="pdf",
        act_name="EPF Act, 1952",
        priority=1,
    ),
    SourceConfig(
        url="https://www.epfindia.gov.in/site_docs/PDFs/Downloads_PDFs/EPFScheme1952.pdf",
        title="Employees' Provident Fund Scheme, 1952",
        source_type="pdf",
        act_name="EPF Act, 1952",
        priority=2,
    ),

    # ─── ESIC ────────────────────────────────────────────────────────────────
    SourceConfig(
        url="https://www.esic.nic.in/attachments/files/ESI-Act1948.pdf",
        title="Employees' State Insurance Act, 1948",
        source_type="pdf",
        act_name="ESI Act, 1948",
        priority=1,
    ),

    # ─── Karnataka Labour Department ─────────────────────────────────────────
    SourceConfig(
        url="https://labour.karnataka.gov.in/English",
        title="Karnataka Labour Department — Official Portal",
        source_type="website",
        priority=2,
    ),
    SourceConfig(
        url="https://labour.karnataka.gov.in/storage/pdf-files/Acts/shops_and_establishment_act.pdf",
        title="Karnataka Shops and Commercial Establishments Act, 1961",
        source_type="pdf",
        act_name="Karnataka Shops and Commercial Establishments Act, 1961",
        priority=1,
    ),

    # ─── BOCW Board Karnataka ────────────────────────────────────────────────
    SourceConfig(
        url="https://bocwkarnataka.in/",
        title="Karnataka Building & Other Construction Workers Board",
        source_type="website",
        priority=2,
    ),

    # ─── National Portals ────────────────────────────────────────────────────
    SourceConfig(
        url="https://eshram.gov.in/",
        title="e-Shram Portal — National Database for Unorganised Workers",
        source_type="website",
        priority=1,
    ),
    SourceConfig(
        url="https://www.pmsby.gov.in/",
        title="Pradhan Mantri Suraksha Bima Yojana",
        source_type="website",
        priority=2,
    ),
    SourceConfig(
        url="https://www.pmjjby.gov.in/",
        title="Pradhan Mantri Jeevan Jyoti Bima Yojana",
        source_type="website",
        priority=2,
    ),
]
