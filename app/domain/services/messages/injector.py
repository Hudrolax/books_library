# domain/services/messages/injector.py
import asyncio
import inspect
import logging
from contextlib import contextmanager
from functools import wraps
from typing import Annotated, get_args, get_origin

logger = logging.getLogger(__name__)

class Depends:
    def __init__(self, dependency):
        self.dependency = dependency


def generator_context(func):
    """
    Преобразует синхронный generator-функцию в contextmanager,
    чтобы поддерживать зависимость через yield.
    """
    @contextmanager
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        try:
            value = next(gen)
        except StopIteration:
            raise RuntimeError("Генератор ничего не yield'ит")
        try:
            yield value
        finally:
            try:
                next(gen)
            except StopIteration:
                pass

    return wrapper


def service_injector(func):
    """
    Декоратор для асинхронных хендлеров:
    - Рекурсивно разрешает и впрыскивает зависимости из sync- и async-генераторов,
      а также обычных функций и корутин с аннотациями Depends.
    - Автоматически вызывает __enter__/__exit__, __anext__ для контекстов.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        sync_ctxs = []       # для sync context managers
        async_gens = []      # для async generators

        async def resolve_dep(dep_func):
            # 1) Синхронный generator -> contextmanager
            if inspect.isgeneratorfunction(dep_func):
                cm = generator_context(dep_func)()
                val = cm.__enter__()
                sync_ctxs.append(cm)
                return val

            # 2) Асинхронный generator
            if inspect.isasyncgenfunction(dep_func):
                agen = dep_func()
                val = await agen.__anext__()
                async_gens.append(agen)
                return val

            # 3) Обычная функция или coroutine, возможно с вложенными Depends
            sig_dep = inspect.signature(dep_func)
            bound_dep = sig_dep.bind_partial()
            kwargs_dep = {}
            for pname, pparam in sig_dep.parameters.items():
                # ищем Depends в default или Annotated
                dep_marker = pparam.default if isinstance(pparam.default, Depends) else None
                if dep_marker is None:
                    pann = pparam.annotation
                    if get_origin(pann) is Annotated:
                        for meta in get_args(pann)[1:]:
                            if isinstance(meta, Depends):
                                dep_marker = meta
                                break
                if dep_marker is None:
                    continue
                # рекурсивно резолвим вложенную зависимость
                kwargs_dep[pname] = await resolve_dep(dep_marker.dependency)

            result = dep_func(**kwargs_dep)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        # Основное разрешение параметров целевой функции
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        injections = dict(bound.arguments)

        for name, param in sig.parameters.items():
            if name in injections:
                continue
            # ищем Depends-маркеры
            dep_marker = param.default if isinstance(param.default, Depends) else None
            if dep_marker is None:
                ann = param.annotation
                if get_origin(ann) is Annotated:
                    for meta in get_args(ann)[1:]:
                        if isinstance(meta, Depends):
                            dep_marker = meta
                            break
            if dep_marker is None:
                continue
            # разрешаем зависимость
            injections[name] = await resolve_dep(dep_marker.dependency)

        # Вызываем оригинальную функцию с готовыми аргументами
        result = func(**injections)
        if asyncio.iscoroutine(result):
            result = await result

        # Завершаем async-генераторы (до StopAsyncIteration)
        for agen in reversed(async_gens):
            try:
                await agen.__anext__()
            except StopAsyncIteration:
                pass
        # Завершаем sync-контексты
        for cm in reversed(sync_ctxs):
            cm.__exit__(None, None, None)

        return result

    return wrapper
