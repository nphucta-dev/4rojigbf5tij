from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cấu hình chuỗi kết nối MySQL (đổi user/password/host/dbname theo môi trường thực tế)
DATABASE_URL = "mysql+pymysql://root:Phucka11%40@localhost:3306/shipments_db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency inject session, tự đóng session sau mỗi request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()