from sqlalchemy.ext.declarative import declarative_base
import ckan.model as model

Base = declarative_base(bind=model.meta.engine)
