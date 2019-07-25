from __future__ import annotations

import random
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Union, List, cast, Optional

from databases import DatabaseURL
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorCollection,
    AsyncIOMotorCursor,
    AsyncIOMotorClientSession,
    AsyncIOMotorLatentCommandCursor,
    AsyncIOMotorChangeStream,
)
from pymongo.errors import BulkWriteError
from pymongo.results import InsertOneResult, InsertManyResult, DeleteResult, UpdateResult
from starlette.requests import Request

from .application import Application

if TYPE_CHECKING:
    from motor.core import (
        AgnosticClient as AsyncIOMotorClient,
        AgnosticDatabase as AsyncIOMotorDatabase,
        AgnosticCollection,
        AgnosticCursor,
        AgnosticClientSession,
        AgnosticLatentCommandCursor,
        AgnosticChangeStream,
    )

    from pymongo.collection import Collection
    from pymongo.cursor import Cursor
    from pymongo.client_session import ClientSession

    AsyncIOMotorCollection = Union[Collection, AgnosticCollection]
    AsyncIOMotorCursor = Union[Cursor, AgnosticCursor]
    AsyncIOMotorClientSession = Union[ClientSession, AgnosticClientSession]
    AsyncIOMotorLatentCommandCursor = Union[AgnosticLatentCommandCursor, AsyncIOMotorLatentCommandCursor]
    AsyncIOMotorChangeStream = Union[AgnosticChangeStream, AsyncIOMotorChangeStream]


@asynccontextmanager
async def begin_transaction(session: AsyncIOMotorClientSession):
    session.start_transaction()

    try:
        yield
    except Exception:
        await session.abort_transaction()
        raise
    else:
        await session.commit_transaction()


class MongoDatabase:
    _database: AsyncIOMotorDatabase
    _session: Optional[AsyncIOMotorClientSession]

    def __init__(self, database: AsyncIOMotorDatabase):
        self._database = database
        self._session = None

    def __getitem__(self, name: str) -> MongoCollection:
        collection = self._database.get_collection(name)
        return MongoCollection(collection, database=self)

    @property
    def client(self) -> AsyncIOMotorClient:
        return cast(AsyncIOMotorClient, self._database.client)

    @property
    def session(self) -> AsyncIOMotorClientSession:
        return self._session

    async def __aenter__(self):
        self._session = await self.client.start_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._session.end_session()
        self._session = None


# noinspection PyShadowingBuiltins
class MongoCollection:
    _database: MongoDatabase
    _collection: AsyncIOMotorCollection
    _session: AsyncIOMotorClientSession

    def __init__(self, collection: AsyncIOMotorCollection, *, database: MongoDatabase):
        self._database = database
        self._collection = collection

    @property
    def database(self) -> MongoDatabase:
        return self._database

    @property
    def session(self) -> AsyncIOMotorClientSession:
        return self.database.session

    async def bulk_write(self, requests, ordered=True, bypass_document_validation=False):
        return await self._collection.bulk_write(requests=requests, ordered=ordered,
                                                 bypass_document_validation=bypass_document_validation,
                                                 session=self.session)

    async def count_documents(self, filter, **kwargs) -> int:
        return await self._collection.count_documents(filter=filter, session=self.session, **kwargs)

    async def create_index(self, keys, **kwargs) -> str:
        return await self._collection.create_index(keys=keys, session=self.session, **kwargs)

    async def create_indexes(self, indexes, **kwargs) -> List[str]:
        return await self._collection.create_indexes(indexes=indexes, session=self.session, **kwargs)

    async def delete_many(self, filter, collation=None) -> DeleteResult:
        return await self._collection.delete_many(filter=filter, collation=collation, session=self.session)

    async def delete_one(self, filter, collation=None) -> DeleteResult:
        return await self._collection.delete_one(filter=filter, collation=collation, session=self.session)

    async def distinct(self, key, filter=None, **kwargs):
        return await self._collection.distinct(key=key, filter=filter, session=self.session, **kwargs)

    async def drop(self) -> None:
        return await self._collection.drop(session=self.session)

    async def drop_index(self, index_or_name, **kwargs) -> None:
        return await self._collection.drop_index(index_or_name=index_or_name, session=self.session, **kwargs)

    async def drop_indexes(self, **kwargs) -> None:
        return await self._collection.drop_indexes(session=self.session, **kwargs)

    async def estimated_document_count(self, **kwargs) -> int:
        return await self._collection.estimated_document_count(**kwargs)

    async def find_one(self, filter=None, *args, **kwargs) -> dict:
        return await self._collection.find_one(filter=filter, *args, **kwargs)

    async def find_one_and_delete(self, filter, projection=None, sort=None, **kwargs) -> dict:
        return await self._collection.find_one_and_delete(filter=filter, projection=projection, sort=sort,
                                                          session=self.session, **kwargs)

    async def find_one_and_replace(self, filter, replacement, projection=None, sort=None, upsert=False,
                                   return_document=False, **kwargs) -> dict:
        return await self._collection.find_one_and_replace(filter=filter, replacement=replacement,
                                                           projection=projection, sort=sort, upsert=upsert,
                                                           return_document=return_document, session=self.session,
                                                           **kwargs)

    async def find_one_and_update(self, filter, update, projection=None, sort=None, upsert=False, return_document=False,
                                  array_filters=None, **kwargs) -> dict:
        return await self._collection.find_one_and_update(filter=filter, update=update, projection=projection,
                                                          sort=sort, upsert=upsert, return_document=return_document,
                                                          array_filters=array_filters, session=self.session, **kwargs)

    async def index_information(self) -> dict:
        return await self._collection.index_information(session=self.session)

    async def inline_map_reduce(self, map, reduce, full_response=False, **kwargs) -> MongoCollection:
        return MongoCollection(
            await self._collection.inline_map_reduce(map=map, reduce=reduce, full_response=full_response,
                                                     session=self.session, **kwargs),
            database=self._database)

    async def insert_many(self, documents, ordered=True, bypass_document_validation=False) -> InsertManyResult:
        return await self._collection.insert_many(documents=documents, ordered=ordered,
                                                  bypass_document_validation=bypass_document_validation,
                                                  session=self.session)

    async def insert_one(self, document, bypass_document_validation=False) -> InsertOneResult:
        return await self._collection.insert_one(document=document,
                                                 bypass_document_validation=bypass_document_validation,
                                                 session=self.session)

    async def map_reduce(self, map, reduce, out, full_response=False, **kwargs):
        return await self._collection.map_reduce(map=map, reduce=reduce, out=out, full_response=full_response,
                                                 session=self.session, **kwargs)

    async def options(self) -> dict:
        return await self._collection.options(session=self.session)

    async def reindex(self, **kwargs):
        return await self._collection.reindex(session=self.session, **kwargs)

    async def rename(self, new_name, **kwargs):
        return await self._collection.rename(new_name=new_name, session=self.session, **kwargs)

    async def replace_one(self, filter, replacement, upsert=False, bypass_document_validation=False,
                          collation=None) -> UpdateResult:
        return await self._collection.replace_one(filter=filter, replacement=replacement, upsert=upsert,
                                                  bypass_document_validation=bypass_document_validation,
                                                  collation=collation, session=self.session)

    async def update_many(self, filter, update, upsert=False, array_filters=None, bypass_document_validation=False,
                          collation=None) -> UpdateResult:
        return await self._collection.update_many(filter=filter, update=update, upsert=upsert,
                                                  array_filters=array_filters,
                                                  bypass_document_validation=bypass_document_validation,
                                                  collation=collation, session=self.session)

    async def update_one(self, filter, update, upsert=False, bypass_document_validation=False, collation=None,
                         array_filters=None) -> UpdateResult:
        return await self._collection.update_one(filter=filter, update=update, upsert=upsert,
                                                 bypass_document_validation=bypass_document_validation,
                                                 collation=collation, array_filters=array_filters, session=self.session)

    def find(self, filter, projection=None, **kwargs) -> AsyncIOMotorCursor:
        return self._collection.find(filter=filter, projection=projection, **kwargs, session=self.session)

    def find_raw_batches(self, *args, **kwargs) -> AsyncIOMotorCursor:
        return self._collection.find_raw_batches(*args, **kwargs, session=self.session)

    def aggregate(self, pipeline, **kwargs) -> AsyncIOMotorLatentCommandCursor:
        return self._collection.aggregate(pipeline, **kwargs)

    def aggregate_raw_batches(self, pipeline, **kwargs) -> AsyncIOMotorLatentCommandCursor:
        return self._collection.aggregate_raw_batches(pipeline, **kwargs)

    def watch(self, pipeline=None, full_document='default', resume_after=None,
              max_await_time_ms=None, batch_size=None, collation=None,
              start_at_operation_time=None) -> AsyncIOMotorChangeStream:
        return self._collection.watch(pipeline=pipeline, full_document=full_document, resume_after=resume_after,
                                      max_await_time_ms=max_await_time_ms, batch_size=batch_size, collation=collation,
                                      start_at_operation_time=start_at_operation_time, session=self.session)

    def list_indexes(self) -> AsyncIOMotorLatentCommandCursor:
        return self._collection.list_indexes(session=self.session)


if TYPE_CHECKING:
    MongoCollection = Union[MongoCollection, AgnosticCollection]
    MongoCursor = Union[MongoCollection, AgnosticCursor]


class DatabasePool:
    def __init__(self, url: DatabaseURL, *, max_size=-1):
        self.url = url
        self.max_size = max_size
        self.pool = []

    async def connect(self) -> AsyncIOMotorClient:
        return AsyncIOMotorClient(
            host=self.url.hostname,
            port=self.url.port,
        )

    async def acquire(self) -> AsyncIOMotorClient:
        if self.pool:
            client = random.choice(self.pool)
            self.pool.remove(client)
            return client
        else:
            return await self.connect()

    async def release(self, client: AsyncIOMotorClient):
        if len(self.pool) < self.max_size:
            self.pool.append(client)
        else:
            client.close()


def init_app(app: Application) -> DatabasePool:
    url = DatabaseURL(app.config.get('DATABASE_URL', 'mongodb:///default'))
    return DatabasePool(url, max_size=32)


def get_pool(app: Application) -> DatabasePool:
    return cast(DatabasePool, app.get_extension(__name__))


@asynccontextmanager
async def connect_database_for(app: Application) -> MongoDatabase:
    pool = get_pool(app)
    client = await pool.connect()

    raw_database = client.get_database(pool.url.database)
    database = MongoDatabase(raw_database)

    try:
        yield database
    finally:
        await pool.release(client)


@asynccontextmanager
async def connect_database(request: Request) -> MongoDatabase:
    app = request.scope['app']
    async with connect_database_for(app) as database:
        request.scope['database'] = database
        yield database


@asynccontextmanager
async def bulk_write_for(collection: MongoCollection, *, ordered: bool) -> List:
    db_ops = []
    yield db_ops

    if db_ops:
        try:
            await collection.bulk_write(db_ops, ordered)
        except BulkWriteError as e:
            print('error', e)
            for db_op in db_ops:
                try:
                    await collection.bulk_write([db_op])
                except Exception:
                    print('failure:', db_op)
                    raise
