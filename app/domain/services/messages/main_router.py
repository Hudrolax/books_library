from domain.services.messages.domain_router import DomainMessageRouter
from domain.services.messages.middlewares import middleware
from domain.services.messages.routers import router as add_link_router

main_router = DomainMessageRouter()
main_router.include_middleware(middleware)
main_router.include_router(add_link_router)
