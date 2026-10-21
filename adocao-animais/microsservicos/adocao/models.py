
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from microsservicos.adocao.database import Base


class Adoption(Base):
    __tablename__ = "adocoes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    animal_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )

    adopter_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    adopter_email: Mapped[str] = mapped_column(
        String(254),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendente",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
