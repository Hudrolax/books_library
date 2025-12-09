import logging
from typing import Optional

from utils.crypto_hash import AbstractCrypto

from ..exceptions import DoubleFoundError, NotFoundError, PermissionException
from ..interfaces.user_ifaces import IUserRepoProtocol, IUserService
from ..models.user import User, UserDict

logger = logging.getLogger(__name__)


class UserService(IUserService):
    repository: IUserRepoProtocol
    wrong_password_ex = NotFoundError("Wrong password or username")

    def __init__(self, repository: IUserRepoProtocol, crypto_hash: AbstractCrypto) -> None:
        self.repository = repository
        self.crypto_hash = crypto_hash

    async def create(
        self,
        user: User,
        username: str,
        password: Optional[str] = None,
        telegram_id: Optional[int] = None,
        level: int = 0,
    ) -> User:
        if user.level < 99:
            raise PermissionException("You do not have permission to create a new user.")

        payload: UserDict = {}
        if username:
            if await self.repository.exists(filters={"username": username}):
                raise DoubleFoundError(f"user with username {username} already exists.")
            payload = {"username": username}

        if password:
            hashed_password = self.crypto_hash.hash(password)
            payload['hashed_password'] = hashed_password
        
        if telegram_id:
            payload['telegram_id'] = telegram_id

        if level:
            payload['level'] = level

        return await self.repository.create(payload)

    async def read(self, filters: UserDict) -> User:
        return await self.repository.read(filters=filters)

    async def verify_password(self, username: str, password: str) -> User:
        user = await self.repository.read(filters={"username": username})
        if self.crypto_hash.verify(password, user.hashed_password):
            return user
        else:
            raise self.wrong_password_ex

    async def update_password(self, username: str, old_password: str, new_password: str) -> User:
        user = await self.repository.read(filters={"username": username})
        if self.crypto_hash.verify(old_password, user.hashed_password):
            hashed_password = self.crypto_hash.hash(new_password)
            updated_users = await self.repository.update(
                filters={"username": username}, data={"hashed_password": hashed_password}
            )
            if len(updated_users) == 1:
                return updated_users[0]
            else:
                raise DoubleFoundError(f"username {username} has a double in DB!")
        else:
            raise self.wrong_password_ex

    async def update(self, user: User, id: int, data: UserDict) -> User:
        if user.level < 99:
            raise PermissionException("You do not have permission to update this user.")

        updated_recors = await self.repository.update(data=data, filters={"id": id})
        if updated_recors == 0:
            raise NotFoundError
        return updated_recors[0]

    async def create_admin_record(self) -> None:
        try:
            await self.repository.read(filters={"username": "admin"})
        except NotFoundError:
            hashed_password = self.crypto_hash.hash("admin")
            await self.repository.create(
                data={"username": "admin", "hashed_password": hashed_password, "level": 99}
            )
            logger.info('Admin user created. Try login with name "admin" and password "admin".')
