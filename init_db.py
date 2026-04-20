from src.database import engine
from src.models import Base

print("Connecting to Neon Database...")
# By importing Base directly from models, we guarantee Python reads the table definitions first
Base.metadata.create_all(bind=engine)
print("All tables successfully created!")