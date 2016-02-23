from sqlalchemy import event, exc, select
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy


class PingConnectionHandler(object):
    """ Handle gone-away connections in the Pool.

    This is mainly taken from the SQLAlchemy documentation.
    """

    def __init__(self, engine):
        self.engine = engine

    def register(self):
        event.listen(self.engine, 'engine_connect', self.ping_connection)

    def ping_connection(self, connection, branch):
        if branch:
            # "branch" refers to a sub-connection of a connection,
            # we don't want to bother pinging on these.
            return

        try:
            # run a SELECT 1.   use a core select() so that
            # the SELECT of a scalar value without a table is
            # appropriately formatted for the backend
            connection.scalar(select([1]))
        except exc.DBAPIError as err:
            # catch SQLAlchemy's DBAPIError, which is a wrapper
            # for the DBAPI's exception.  It includes a .connection_invalidated
            # attribute which specifies if this connection is a "disconnect"
            # condition, which is based on inspection of the original exception
            # by the dialect in use.
            if err.connection_invalidated:
                # run the same SELECT again - the connection will re-validate
                # itself and establish a new connection.  The disconnect detection
                # here also causes the whole connection pool to be invalidated
                # so that all stale connections are discarded.
                connection.scalar(select([1]))
            else:
                raise


class SQLAlchemy(_SQLAlchemy):
    def init_app(self, app):
        super().init_app(app)
        if app.config.get('SQLALCHEMY_DISCONNECTION_HANDLING', True):
            PingConnectionHandler(self.get_engine(app)).register()
