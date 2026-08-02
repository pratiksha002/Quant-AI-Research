import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, LargeBinary, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BatchHistory(Base):
    __tablename__ = 'batch_history'
    
    id = Column(Integer, primary_key=True, index=True)
    batch_uuid = Column(String(36), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    files = relationship("FileConversion", back_populates="batch")

class FileConversion(Base):
    __tablename__ = 'file_conversions'
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey('batch_history.id'))
    original_filename = Column(String(255))
    file_type = Column(String(50))
    
    # Store the actual files in the database
    original_file_data = Column(LargeBinary, nullable=True) 
    md_content = Column(Text, nullable=True) 
    
    status = Column(String(50), default='pending') # pending, processing, completed, failed
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    batch = relationship("BatchHistory", back_populates="files")