import sqlalchemy
import sqlalchemy.orm
import enum
from .db import Base

class Roles(enum.Enum):
    admin = 1
    uploaders = 2
    viewers = 3

class User(Base):
    
    __tablename__ = "user"
    
    username = sqlalchemy.Column(sqlalchemy.String, primary_key=True, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String)
    salt = sqlalchemy.Column(sqlalchemy.String)
    session = sqlalchemy.Column(sqlalchemy.UUID, unique=True)
    roles = sqlalchemy.Column(sqlalchemy.Enum(Roles))
    
class Folder(Base):
    
    __tablename__ = "folder"
    
    name = sqlalchemy.Column(sqlalchemy.String)
    accessers = sqlalchemy.Column(sqlalchemy.ARRAY(sqlalchemy.String))
    id = sqlalchemy.Column(sqlalchemy.UUID, unique=True, primary_key=True)
    
class File(Base):
    
    __tablename__ = "file"
    
    folder = sqlalchemy.Column(sqlalchemy.UUID, sqlalchemy.ForeignKey("folder.id"))
    id = sqlalchemy.Column(sqlalchemy.UUID, unique=True)
    last_updated = sqlalchemy.Column(sqlalchemy.DateTime)
    path = sqlalchemy.Column(sqlalchemy.String)
    name = sqlalchemy.Column(sqlalchemy.String)
    who = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey("user.username"))