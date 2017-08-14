from asyncpg import InterfaceError, create_pool
from asyncpg.pool import Pool


async def make_tables(pool: Pool, schema: str):
        """
        Make tables if they don't exist.
        :param pool: the connection pool.
        :param schema: the schema name.
        """
        await pool.execute('CREATE SCHEMA IF NOT EXISTS {};'.format(schema))

        servers = """
        CREATE TABLE IF NOT EXISTS {}.servers (
        server INT,
        expanded BOOLEAN,
        stats BOOLEAN,
        PRIMARY KEY (server)
        );""".format(schema)

        requests = """
        CREATE TABLE IF NOT EXISTS {}.requests (
        id SERIAL,
        requester BIGINT,
        server BIGINT,
        medium SMALLINT,
        title VARCHAR NOT NULL,
        PRIMARY KEY (id, requester, server)
        );
        """.format(schema)

        await pool.execute(servers)
        await pool.execute(requests)


class PostgresController():
    """
    To be able to integrate with an existing database, all tables for
    discordoragi will be put under the `discordoragi` schema unless a
    different schema name is passed to the __init__ method.
    """
    __slots__ = ('pool', 'schema', 'logger')

    def __init__(self, pool: Pool, logger, schema: str = 'discordoragi'):
        """
        Init method. Create the instance with the `get_instance` method to make
        sure you have all the tables needed.
        :param pool: the `asyncpg` connection pool.
        :param logger: logger object used for logging.
        :param schema: the schema name, default is `discordoragi`
        """
        self.pool = pool
        self.schema = schema
        self.logger = logger

    @classmethod
    async def get_instance(cls, logger, connect_kwargs: dict = None,
                           pool: Pool = None, schema: str = 'discordoragi'):
        """
        Get a new instance of `PostgresController`
        This method will create the appropriate tables needed.
        :param logger: the logger object.
        :param connect_kwargs:
            Keyword arguments for the
            :func:`asyncpg.connection.connect` function.
        :param pool: an existing connection pool.
        One of `pool` or `connect_kwargs` must not be None.
        :param schema: the schema name used. Defaults to `discordoragi`
        :return: a new instance of `PostgresController`
        """
        assert connect_kwargs or pool, (
            'Please either provide a connection pool or '
            'a dict of connection data for creating a new '
            'connection pool.'
        )
        if not pool:
            try:
                pool = await create_pool(**connect_kwargs)
                logger.info('Connection pool made.')
            except InterfaceError as e:
                logger.error(str(e))
                raise e
        logger.info('Creating tables...')
        await make_tables(pool, schema)
        logger.info('Tables created.')
        return cls(pool, logger, schema)