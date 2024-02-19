import datetime
import typing

from asyncpg import Record


class RecordWithGetAttributeIncluded(Record):
    def __getattr__(self, name):
        return self[name]


class UserRecord(RecordWithGetAttributeIncluded):
    """
    Attributes:
        username (str): Username
        password (str): Password (Salted)
        salt (str): Salt that is used to hash a password
        session (str): UUID of the session (only one session per device)
        roles (str): Role of the user
    """

    username: str
    "Username"

    password: str
    "Password (Salted)"

    salt: str
    "Salt that is used to hash a password"

    session: str
    "UUID of the session (only one session per device)"

    roles: typing.Literal["admin", "uploaders", "viewers"]
    "Role of the user"


class FolderRecord(RecordWithGetAttributeIncluded):
    """
    Attributes:
        name (str): Folder Name
        accessers (list[str]): List of users that can access this folder
        id (str): UUID of the folder
    """

    name: str
    "Folder Name"

    accessers: list[str]
    "List of users that can access this folder"

    id: str
    "UUID of the folder"


class FileRecord(RecordWithGetAttributeIncluded):
    """
    Attributes:
        folder (str): Folder Name
        id (str): UUID of the file
        last_updated (str): Date of the file being updated
        path (str): The file path
    """

    folder: str
    "Folder Name"

    id: str
    "UUID of the file"

    last_updated: datetime.datetime
    "Date of the file being updated"

    path: str
    "The file path"

    name: str
    "File Name"
    
    who: str
    "Which user uploaded this file"