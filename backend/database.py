from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

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


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    event = Column(String, nullable=False)
    detail = Column(String, nullable=True)
    timestamp = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)