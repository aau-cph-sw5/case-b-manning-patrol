from uuid import UUID

from sqlmodel import Field, SQLModel


class TrainLine(SQLModel, table=True):
    train_id: UUID = Field(foreign_key="train.id", primary_key=True)
    line_id: str = Field(foreign_key="line.id", primary_key=True)
