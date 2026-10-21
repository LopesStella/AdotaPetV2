
import os

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "postgres"),
    query={"sslmode": os.getenv("DB_SSLMODE", "require")},
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
