import uuid

from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.models import User

logger = get_logger('seed')


def seed_default_user(db_session) -> None:
    existing = db_session.query(User).filter(User.email == 'admin@pharma.ai').first()
    if existing:
        return

    default_user = User(
        id=str(uuid.uuid4()),
        email='admin@pharma.ai',
        full_name='Admin User',
        hashed_password=hash_password('admin123'),
    )
    db_session.add(default_user)
    db_session.commit()
    logger.info('Default test user created', extra={'route': 'startup'})
