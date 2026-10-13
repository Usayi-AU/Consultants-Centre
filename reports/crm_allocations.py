"""Client CRM allocations (Main CRM / Alternate CRM) from the Client Allocations sheet.

Keys are client names as stored in the trackers; values are (main CRM, alternate CRM).
"""

CLIENT_CRM_ALLOCATIONS = {
    "ABC": ("Tariro", "Tatenda"),
    "AGS": ("Arnold", "Tariro"),
    "Allied Timbers": ("Arnold", "Tatenda"),
    "Astra Industries PF": ("Arnold", "Tatenda"),
    "BOC Pension Fund": ("Tatenda", "Tariro"),
    "BPB Gypsum / Saint Gobain": ("Godfrey", "Tinotenda"),
    "Brands Africa": ("Elvis", "Tatenda"),
    "Marsh Employees PF": ("Elvis", "Tinotenda"),
    "CAAZ": ("Tariro", "Godfrey"),
    "CIPF": ("Tatenda", "Tinotenda"),
    "Dairibord": ("Tatenda", "Tariro"),
    "Datlabs Pension Fund": ("Tinotenda", "Elvis"),
    "Econet": ("Tariro", "Tinotenda"),
    "Edgars Actives PF": ("Tinotenda", "Tariro"),
    "Edgars Pensioners PF": ("Tinotenda", "Tariro"),
    "EY Pension Fund": ("Godfrey", "Tinotenda"),
    "Falcon College PF": ("Tinotenda", "Elvis"),
    "FBC": ("Tatenda", "Tinotenda"),
    "Fintrust - Risk": ("Godfrey", "Tariro"),
    "FCB PF (formerly Barclays PF)": ("Tariro", "Tatenda"),
    "Freda Rebecca": ("Tatenda", "Tariro"),
    "Getbucks": ("Arnold", "Tinotenda"),
    "Haggie Rand PF": ("Tatenda", ""),
    "Hippo": ("Tariro", "Tatenda"),
    "IDBZ": ("Tatenda", "Tinotenda"),
    "Innscor Pension Fund": ("Tariro", "Tinotenda"),
    "Investor Protection Fund - Investments": ("Tariro", "Tinotenda/Owen"),
    "Investor Protection Fund - Risk": ("Tariro", "Godfrey/Owen"),
    "Larfarge PF (Actives)": ("Tatenda", "Tinotenda"),
    "Larfarge PF (Pensioners)": ("Tatenda", "Tinotenda"),
    "Mashonaland Tobacco Company": ("Tariro", "Tatenda"),
    "Masiyephambili Schools Trust PF": ("Tinotenda", "Elvis"),
    "MCAZ": ("Elvis", "Tinotenda"),
    "Mimosa Mining PF": ("Tariro", "Elvis"),
    "Mimosa Corporate Funds": ("Tinotenda", "Tariro"),
    "Minerva Copvol PF": ("Tinotenda", "Tatenda"),
    "Minerva Income Withdrawal Fund": ("Tinotenda", "Tatenda"),
    "Minerva Provident": ("Tinotenda", "Tatenda"),
    "Minerva Risk Advisors": ("Tinotenda", "Tatenda"),
    "Minerva Umbrella Fund": ("Tinotenda", "Tatenda"),
    "NBS": ("Elvis", "Tariro"),
    "Nestle": ("Tariro", "Tinotenda"),
    "NOIC Pension Fund": ("Tariro", "Arnold"),
    "NSSA": ("Tariro", "Tatenda"),
    "Petrotrade Pension Fund": ("Godfrey", "Tariro"),
    "PSMAS": ("Tatenda", "Tariro"),
    "Sandvik Pension Fund": ("Elvis", "Tariro"),
    "Seedco": ("Godfrey", "Tatenda"),
    "Shamwa Gold Mine": ("Tatenda", "Tariro"),
    "Shangani Holistic": ("Godfrey", "Tatenda"),
    "Simbisa": ("Tariro", "Tinotenda"),
    "St Johns": ("Elvis", "Tariro"),
    "Stanbic": ("Tatenda", "Tariro"),
    "Stanchart Pension Fund": ("Tatenda", "Tinotenda"),
    "Telecel": ("Arnold", "Tariro"),
    "TIMB Pension Fund": ("Tariro", "Tinotenda"),
    "TRB": ("Elvis", "Tatenda"),
    "Triangle PF - The Money Plan": ("Tariro", "Tatenda"),
    "Triangle Senior Staff": ("Tariro", "Tatenda"),
    "Unicem PF (Actives)": ("Tinotenda", "Godfrey"),
    "Unicem PF (Pensioners)": ("Tinotenda", "Godfrey"),
    "Unilever Zimbabwe PF": ("Tariro", "Tinotenda"),
    "Vivo Energy": ("Godfrey", "Tariro"),
    "Whitestone School Trust PF": ("Tinotenda", "Elvis"),
    "Zambezi River Authority": ("Tatenda", "Elvis"),
    "Zimasco Pension Fund": ("Arnold", "Tinotenda"),
    "Zimnat Group Staff PF": ("Tatenda", "Tinotenda"),
    "Zimnat Life Assurance": ("Tatenda", "Tinotenda"),
    "Zimplow": ("Arnold", "Tatenda"),
    "Zimsec Pension Fund": ("Tatenda", "Godfrey"),
    "The Joseph Pension Fund": ("Tatenda", "Tariro"),
    "Goldridge": ("Tatenda", "Tariro"),
    "United Refineries": ("Tariro", "Arnold"),
    "Girls College": ("Tinotenda", "Elvis"),
}

# Clients on the allocation sheet that may not exist in the trackers yet.
NEW_CLIENTS = ("Zimnat Life Assurance",)

# Short names previously used on the dashboards, for clients not on the sheet.
CRM_NAME_RENAMES = {"Tari": "Tariro", "Tino": "Tinotenda"}


def apply_crm_allocations(ClientReport, SharePointTrackerEntry):
    """Apply the allocation sheet to every quarter of both trackers. Safe to re-run."""
    for model in (ClientReport, SharePointTrackerEntry):
        has_alternate = model is SharePointTrackerEntry
        for old_name, new_name in CRM_NAME_RENAMES.items():
            model.objects.filter(crm_name=old_name).update(crm_name=new_name)
            if has_alternate:
                model.objects.filter(alternate_name=old_name).update(alternate_name=new_name)

        for client_name, (main_crm, alternate_crm) in CLIENT_CRM_ALLOCATIONS.items():
            fields = {"crm_name": main_crm}
            if has_alternate:
                fields["alternate_name"] = alternate_crm
            model.objects.filter(client_name=client_name).update(**fields)

        quarters = model.objects.values_list("quarter", flat=True).distinct()
        for quarter in quarters:
            for client_name in NEW_CLIENTS:
                if model.objects.filter(quarter=quarter, client_name=client_name).exists():
                    continue
                main_crm, alternate_crm = CLIENT_CRM_ALLOCATIONS[client_name]
                fields = {"quarter": quarter, "client_name": client_name, "crm_name": main_crm}
                if has_alternate:
                    fields["alternate_name"] = alternate_crm
                else:
                    fields["operations_assignee"] = "Unassigned"
                model.objects.create(**fields)
