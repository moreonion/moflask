"""Tests for the sqlalchemy sub-module."""

import datetime
import os
from unittest import mock

import flask_sqlalchemy
import pytest
import pytz
import sqlalchemy as sa
from sqlalchemy import orm

from moflask import flask, sqlalchemy

db_conn = flask_sqlalchemy.SQLAlchemy()


class Example(db_conn.Model):
    """An example db table with a date field."""

    # pylint: disable=too-few-public-methods
    id: orm.Mapped[int] = orm.mapped_column(sa.Identity(), primary_key=True)
    created_at: orm.Mapped[datetime.datetime] = orm.mapped_column(sqlalchemy.DateTimeUTC)


@pytest.fixture(name="app", scope="class")
def fixture_app():
    """Create new app instance."""
    with mock.patch.dict(os.environ, {"FLASK_SETTINGS": "settings/testing.py"}):
        app = flask.BaseApp("sa_test")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URI"]
    with app.app_context():
        yield app


@pytest.fixture(name="db", scope="class")
def fixture_db(app):
    """Bind db to app and create / drop tables."""
    db_conn.init_app(app)
    db_conn.create_all()
    yield db_conn
    db_conn.session.remove()
    db_conn.reflect()
    db_conn.drop_all()


def test_error_for_native_datetime_objects(db):
    """Test that using native datetime objects raises an exception."""
    with pytest.raises(sa.exc.StatementError):
        row = Example(created_at=datetime.datetime.now())
        db.session.add(row)
        db.session.commit()


def test_time_is_preserved(db):
    """Test that times are preserved when saving and loading."""
    timezone_aware_now = datetime.datetime.now(datetime.timezone.utc)
    row = Example(created_at=timezone_aware_now)
    db.session.add(row)
    db.session.commit()
    assert row.created_at == timezone_aware_now
    assert row.created_at.tzinfo == datetime.timezone.utc


def test_timezone_is_converted_to_utc(db):
    """Test that UTC datetimes are returned regardless of input."""
    timezone_aware_now = datetime.datetime.now(pytz.timezone("Europe/Vienna"))
    row = Example(created_at=timezone_aware_now)
    db.session.add(row)
    db.session.commit()
    assert row.created_at == timezone_aware_now
    assert row.created_at == timezone_aware_now.astimezone(datetime.timezone.utc)
    assert row.created_at.tzinfo == datetime.timezone.utc
