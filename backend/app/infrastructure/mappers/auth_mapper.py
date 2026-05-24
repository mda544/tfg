from app.infrastructure.orm_models import UserORM
from app.api.schemas.models import TokenDTO


def user_to_token_dto(user: UserORM, token: str) -> TokenDTO:
    return TokenDTO(access_token=token, user_id=user.id, username=user.username)
