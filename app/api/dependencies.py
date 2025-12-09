from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.interfaces.user_ifaces import IUserRepoProtocol, IUserService
from domain.models.user import User
from domain.services.user_service import UserService
from infrastructure.db.db import get_db
from infrastructure.db.models.user_orm import UserORM
from infrastructure.repositories.user_repo import UserRepo
from utils.crypto_hash import AbstractCrypto, Argon2Crypto


def crypto_hash_factory() -> AbstractCrypto:
    return Argon2Crypto()


# ****** User dependencies ******
def user_repo_factory(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IUserRepoProtocol:
    return UserRepo(db, domain_model=User, orm_class=UserORM)


def get_user_service(repo: IUserRepoProtocol = Depends(user_repo_factory)) -> IUserService:
    return UserService(repository=repo, crypto_hash=crypto_hash_factory())
