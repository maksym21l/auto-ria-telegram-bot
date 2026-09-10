from db import Base
from sqlalchemy import Column, Integer


class Filter(Base):
    __tablename__ = "filters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    min_price = Column(Integer)
    max_price = Column(Integer)
    min_year = Column(Integer)
    max_year = Column(Integer)
    city = Column(Integer)

    page_count = Column(Integer, default=0)

