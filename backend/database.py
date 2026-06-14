from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///zerotrust.db")

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    public_key = Column(String, nullable=False)


class DeviceProfile(Base):
    __tablename__ = "device_profiles"

    user_id = Column(String, primary_key=True)
    trusted_ip = Column(String, nullable=False)
    agent_required = Column(Boolean, default=True)


Base.metadata.create_all(bind=engine)