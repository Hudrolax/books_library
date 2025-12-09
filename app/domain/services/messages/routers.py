import json
import re
from typing import Annotated

from domain.exceptions import DoubleFoundError, MessageRouterException
from domain.interfaces import IAgent, ILinkService
from domain.models import Context, Message

from .dependencies import get_link_service
from .domain_router import DomainMessageRouter
from .injector import Depends

router = DomainMessageRouter()


@router.message(lambda m: m.text.lower() in ['status', 'state', 'статус'])
async def status_router(msg: Message):
    answer = 'Заглушка для статуса'
    await msg.answer(Message(text=answer))
    msg.context.append(
        Context(username=msg.data['user'].username, user_text=msg.text, jarvis_text=answer)
    )

    raise MessageRouterException


# @router.message(lambda m: bool(re.compile(r'https?://\S+').search(m.text)))
# async def add_link_by_agent(
#     msg: Message,
#     agent: Annotated[IAgent, Depends(get_add_link_agent)]
# ):
#     print('add link by agent')
#     response: Message = await agent.invoke(msg)
#     await msg.answer(response)
#     msg.context.append(
#         Context(username=msg.data['user'].username, user_text=msg.text, jarvis_text=response.text)
#     )
#     # raise MessageRouterException


@router.message(lambda m: bool(re.compile(r'https?://\S+').search(m.text)))
async def add_link_by_algorithm(
    msg: Message,
    link_service: Annotated[ILinkService, Depends(get_link_service)]
):
    # Если агент недоступен - добавляем ссылку алгоритмически
    link_str = re.compile(r'https?://\S+').search(msg.text).group(0)  # type: ignore
    try:
        await link_service.append({
            'user_id': msg.data['user'].id,
            'link': link_str,
            'description': (''+msg.text).replace(link_str, '').strip(),
        })
        response = Message(text='Добавил ссылку в базу данных.')
        await msg.answer(response)
        msg.context.append(
            Context(username=msg.data['user'].username, user_text=msg.text, jarvis_text=response.text)
        )
    except DoubleFoundError:
        link = await link_service.read(filters={'link': link_str})
        answer = f'В БД уже есть такая ссылка. Вот ее описание: {link.description}'
        await msg.answer(Message(text=answer))
        msg.context.append(
            Context(username=msg.data['user'].username, user_text=msg.text, jarvis_text=answer)
        )


@router.message()
async def last_router(msg: Message):
    await msg.answer(Message(text='Не нашел, что тебе ответить'))
    await msg.answer(Message(text=json.dumps([u.model_dump() for u in msg.context], ensure_ascii=False)))
