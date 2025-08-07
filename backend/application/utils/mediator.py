from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type, Self

from backend.service.dependency_injection import container

TRequest = TypeVar('TRequest')
TResponse = TypeVar('TResponse')

class Request(ABC, Generic[TResponse]):
    pass

class RequestHandler(ABC, Generic[TRequest, TResponse]):
    @abstractmethod
    def handle(self, request: TRequest) -> TResponse:
        pass

class Mediator:
    __handler_mapping: dict[Type[Request], Type[RequestHandler]]

    def __init__(self) -> None:
        self.__handler_mapping = {}

    def register(self, request_type: Type[Request[TResponse]], handler_type: Type[RequestHandler[TRequest, TResponse]]) -> Self:
        container.register(handler_type)
        self.__handler_mapping[request_type] = handler_type

        return self

    def send(self, request: Request[TResponse]) -> TResponse:
        request_type = type(request)
        handler = self.__handler_mapping.get(request_type)

        if handler is None:
            raise Exception(f'Handler for {request_type} hasn\'t been registered!')

        return container.resolve(handler).handle(request)
