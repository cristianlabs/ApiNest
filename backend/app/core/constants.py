import enum


class Role(str, enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class MembershipStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
