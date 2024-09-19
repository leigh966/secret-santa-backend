from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from db import db

class Group(db.Model):
    __tablename__="group"
    group_id: Mapped[str] = mapped_column(primary_key=True)
    group_name: Mapped[str] = mapped_column(nullable=False)
    game_id: Mapped[str] = mapped_column(nullable=False)