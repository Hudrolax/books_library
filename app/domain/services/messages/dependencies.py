from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from domain.interfaces import (
    IEmbeddingClient,
    IEmbeddingService,
    ILinkRepoProtocol,
    ILinkService,
    IUserRepoProtocol,
    IUserService,
)
from domain.models import Link, User
from domain.services import EmbeddingService, LinkService, UserService
from infrastructure.clients import OpenAIEmbeddingClient
from infrastructure.db.db import get_db
from infrastructure.db.models import LinkORM, UserORM
from infrastructure.repositories import LinkRepo, UserRepo
from utils.crypto_hash import AbstractCrypto, Argon2Crypto

from .injector import Depends


def crypto_hash_factory() -> AbstractCrypto:
    return Argon2Crypto()


# ****** User dependencies ******
def user_repo_factory(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IUserRepoProtocol:
    return UserRepo(db, domain_model=User, orm_class=UserORM)


def get_user_service(repo: Annotated[IUserRepoProtocol, Depends(user_repo_factory)]) -> IUserService:
    return UserService(repository=repo, crypto_hash=crypto_hash_factory())


# ****** Link dependencies ******
def link_repo_factory(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ILinkRepoProtocol:
    return LinkRepo(db, domain_model=Link, orm_class=LinkORM)


def embedding_client_factory() -> IEmbeddingClient:
    return OpenAIEmbeddingClient(api_key=settings.OPENAI_API_KEY)


def get_link_service(
    repo: Annotated[ILinkRepoProtocol, Depends(link_repo_factory)],
    embedding_client: Annotated[IEmbeddingService, Depends(embedding_client_factory)],
) -> ILinkService:
    return LinkService(repository=repo, embed_service=EmbeddingService(client=embedding_client))

