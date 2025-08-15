from dataclasses import dataclass

from backend.application.utils.mediator import Request, RequestHandler
from backend.domain.services.context_manager_service import ContextManagerService


@dataclass
class ToggleRepeatCommand(Request[None]):
    pass

class ToggleRepeatCommandHandler(RequestHandler[ToggleRepeatCommand, None]):
    __context_manager_service: ContextManagerService

    def __init__(self, context_manager_service: ContextManagerService) -> None:
        self.__context_manager_service = context_manager_service

    def handle(self, request: ToggleRepeatCommand) -> None:
        queue_state = self.__context_manager_service.get_queue_state()
        queue_state.toggle_repeat()
