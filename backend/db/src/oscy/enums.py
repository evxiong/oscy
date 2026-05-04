from enum import Enum


class UpdateType(str, Enum):
    nominations = "nominations"
    unofficial = "unofficial"
    official = "official"
