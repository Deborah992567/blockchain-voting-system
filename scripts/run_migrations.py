"""Helper to run Alembic migrations programmatically."""
from alembic.config import Config
from alembic import command
import os

here = os.path.dirname(__file__)
alembic_cfg = Config(os.path.join(os.path.dirname(here), '..', 'alembic.ini'))

def upgrade_head():
    command.upgrade(alembic_cfg, 'head')

if __name__ == '__main__':
    upgrade_head()
    print('Migrations applied (head)')
