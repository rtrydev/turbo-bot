from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.services.context_manager_service import ContextManagerService


class ClearQueueCommand(Request[None]):
    pass

class ClearQueueCommandHandler(RequestHandler[ClearQueueCommand, None]):
    __context_manager_service: ContextManagerService

    def __init__(self, context_manager_service: ContextManagerService) -> None:
        self.__context_manager_service = context_manager_service

    def handle(self, request: ClearQueueCommand) -> None:
        queue_state = self.__context_manager_service.get_queue_state()
        queue_state.clear()
