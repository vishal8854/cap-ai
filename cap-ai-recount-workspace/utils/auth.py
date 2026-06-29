ROLES = {
    "Admin": {"recount": True, "round_trip": True, "interest": True, "idle": True, "signatory": True, "import": True, "reports": True, "settings": True},
    "Auditor": {"recount": True, "round_trip": True, "interest": True, "idle": True, "signatory": True, "import": True, "reports": True, "settings": False},
    "Observer": {"recount": True, "round_trip": False, "interest": False, "idle": False, "signatory": False, "import": False, "reports": True, "settings": False},
}


def can_access(role: str, module: str) -> bool:
    perms = ROLES.get(role, ROLES["Observer"])
    return perms.get(module, False)
