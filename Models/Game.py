from sqlalchemy import DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db import db

class Game(db.Model):
    __tablename__="game"
    game_id: Mapped[str] = mapped_column(primary_key=True)
    draw_date: Mapped[datetime] = mapped_column(DateTime(), nullable=False)
    drawn: Mapped[bool] = mapped_column(default=False)