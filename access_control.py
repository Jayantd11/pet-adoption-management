ROLE_SECTIONS = {
    "pending": {"dashboard"},
    "staff":   {"dashboard", "medical","reports"},
    "manager": {"dashboard", "add", "manage", "medical", "staff", "reports"},
    "admin":   {"dashboard", "add", "manage", "medical", "staff", "user_admin", "reports"},
}


def can_access(role: str, section_key: str) -> bool:
    allowed = ROLE_SECTIONS.get(role, set())
    return section_key in allowed
