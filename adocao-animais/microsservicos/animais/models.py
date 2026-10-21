
import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from microsservicos.animais.database import Base


class Animal(Base):
    __tablename__ = "animais"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    species: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    breed: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    age_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    reservation_adoption_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )
