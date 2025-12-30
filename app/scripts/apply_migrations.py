"""Fallback migration runner using SQLAlchemy DDL.

This script attempts to apply the schema changes when Alembic/CLI is not available.
It is intended for development/testing environments only.
"""
try:
    from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, inspect, text
    from app.database.session import engine
    from app.utils.logger import logger as base_logger
except Exception as exc:
    print("Failed to import application modules. Ensure you run this from the backend directory with PYTHONPATH=. and a compatible Python environment.")
    print("Recommended: create a virtualenv and install backend dependencies (see backend/requirements.txt if present).")
    raise


logger = base_logger.bind(context="scripts.apply_migrations")


def ensure_table_exists():
    meta = MetaData()
    insp = inspect(engine)

    # create association table election_admins if missing
    if 'election_admins' not in insp.get_table_names():
        logger.info("Creating table election_admins")
        t = Table('election_admins', meta,
                  Column('election_id', Integer, ForeignKey('elections.id'), primary_key=True, nullable=False),
                  Column('user_id', Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
                  )
        meta.create_all(bind=engine, tables=[t])
    else:
        logger.info('association table election_admins already exists')


def ensure_columns():
    insp = inspect(engine)
    # elections table
    cols = [c['name'] for c in insp.get_columns('elections')]
    with engine.connect() as conn:
        if 'name' not in cols:
            logger.info('Adding column elections.name')
            conn.execute(text('ALTER TABLE elections ADD COLUMN name VARCHAR'))
        else:
            logger.info('elections.name exists')

        if 'contract_address' not in cols:
            logger.info('Adding column elections.contract_address')
            conn.execute(text('ALTER TABLE elections ADD COLUMN contract_address VARCHAR'))
        else:
            logger.info('elections.contract_address exists')

    # votes table
    cols = [c['name'] for c in insp.get_columns('votes')]
    with engine.connect() as conn:
        if 'signature' not in cols:
            logger.info('Adding column votes.signature')
            conn.execute(text('ALTER TABLE votes ADD COLUMN signature VARCHAR'))
        else:
            logger.info('votes.signature exists')

        if 'tx_hash' not in cols:
            logger.info('Adding column votes.tx_hash')
            conn.execute(text('ALTER TABLE votes ADD COLUMN tx_hash VARCHAR'))
        else:
            logger.info('votes.tx_hash exists')

        if 'wallet_address' not in cols:
            logger.info('Adding column votes.wallet_address')
            conn.execute(text('ALTER TABLE votes ADD COLUMN wallet_address VARCHAR'))
        else:
            logger.info('votes.wallet_address exists')


def main():
    logger.info('Starting fallback migration')
    try:
        ensure_table_exists()
        ensure_columns()
    except Exception:
        logger.exception('Failed to apply fallback migrations')
        raise
    logger.info('Fallback migration completed')


if __name__ == '__main__':
    main()
