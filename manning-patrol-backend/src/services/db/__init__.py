from sqlmodel import SQLModel, Session, create_engine
from uuid import UUID
from src.models import Datasheet
DATABASE_URL = "sqlite:///./dev.db"
engine = create_engine(DATABASE_URL, echo=True)

# This is a one-shot create and fill db with entries for returning payload to phone
def init_db():
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        count = session.exec(Datasheet).count()
        if count == 0:
            entries = [
                Datasheet(
                    beacon_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
                    station="Central Station",
                    concourse=True,
                    platform=False
                ),
                Datasheet(
                    beacon_id=UUID("550e8400-e29b-41d4-a716-446655440001"),
                    station="North Station",
                    concourse=False,
                    platform=True
                )
            ]

            for entry in entries:
                session.add(entry)

            session.commit()


def get_session():
    with Session(engine) as session:
        yield session
