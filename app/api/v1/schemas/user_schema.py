from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    telegram_id: int | None
    level: int

class UserCreateSchema(UserBase):
    password: str
    level: int = 0

class UserLoginSchema(BaseModel):
    username: str
    password: str

class UserReadSchema(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class UserTokenSchema(UserReadSchema):
    token: str

class UserUpdatePasswordSchema(BaseModel):
    old_password: str
    new_password: str
