from sqlalchemy.orm import Mapped, mapped_column
from db import db


class Player(db.Model):
    __tablename__="player"
    player_id: Mapped[str] = mapped_column(primary_key=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)
    player_name:Mapped[str] = mapped_column(nullable=False)
    picked_name:Mapped[str] = mapped_column(nullable=False)
    group_id:Mapped[str] = mapped_column(nullable=False)