"""Define SQLAlchemy column types and decorators."""

import datetime
import typing as t

import sqlalchemy as sa


class DateTimeUTC(sa.types.TypeDecorator):
    """SQLAlchemy type for storing datetime objects in UTC."""

    # pylint: disable=too-many-ancestors

    cache_ok = True
    impl = sa.DateTime

    def process_bind_param(self, value: t.Optional[datetime.datetime], dialect):
        """Process values before they are passed to the database."""
        if value is None:
            return None
        if value.tzinfo and value.tzinfo.utcoffset(value) is not None:
            return value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        raise TypeError("Only timezone aware datetime objects are supported.")

    def process_literal_param(self, value, dialect):
        """Implement abstract method.

        Calling process_bind_param is the default behaviour anyway but an implementation of the
        abstract method is still required.
        """
        return self.process_bind_param(value, dialect)

    def process_result_value(self, value: t.Optional[datetime.datetime], dialect):
        """Process values returned by the database."""
        if value is None:
            return None
        return value.replace(tzinfo=datetime.timezone.utc)

    @property
    def python_type(self):
        """Return the Python type object expected.

        The same type as sa.types.DateTime.
        """
        return datetime.datetime
