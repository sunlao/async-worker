from http import HTTPStatus, HTTPMethod
from uuid import UUID
from types import MappingProxyType
from typing import Mapping, Any
from fastapi import Response, Request
from shared.models.api import ASGIEvent, Routes, APIEvent
from shared.models.log import Core, Event


class LogSerializer:
    """Help API Service get attributes used for logging DTOs"""

    @staticmethod
    def _freeze_path_params(params: Mapping[str, Any] | None) -> Mapping[str, str]:
        if not params:
            return MappingProxyType({})
        params_str = {str(k): str(v) for k, v in dict(params).items()}
        return MappingProxyType(params_str)

    @staticmethod
    def _method(p_request: Request) -> HTTPMethod:
        method = p_request.scope["method"]
        return HTTPMethod[method]

    def _path_params(self, p_request: Request) -> Mapping[str, str]:
        params = getattr(p_request, "path_params", None)
        return self._freeze_path_params(params)

    @staticmethod
    def _routes(p_request: Request) -> Routes:
        route_obj = p_request.scope.get("route")
        template = (
            getattr(route_obj, "path", None)
            or getattr(p_request.url, "path", "Not Defined")
            or "Not Defined"
        )
        name = route_obj.name if route_obj and route_obj.name else "Not Defined"
        path = p_request.scope["path"]
        return Routes(RoutePathTemplate=template, RouteName=name, RequestPath=path)

    @staticmethod
    def _status(p_response: Response) -> HTTPStatus:
        status_code = int(getattr(p_response, "status_code", 500))
        return HTTPStatus(status_code)

    def message(self, p_response: Response) -> str:
        """Help main get a Clean message for Core logging. Use status if noting in body.
        Limit to 2k Characters"""
        status = self._status(p_response)
        body = getattr(p_response, "body", b"")
        if isinstance(body, (bytes, bytearray)):
            msg = body.decode("utf-8", errors="replace").strip()
        else:
            msg = (str(body) if body is not None else "").strip()
        if not msg:
            msg = str(status)
        return msg[:2000]

    def build(self, core_dto: Core, asgi_event_dto: ASGIEvent) -> Event:
        """Build Middleware events into a logging DTO"""
        routes = self._routes(asgi_event_dto.Request)
        status = self._status(asgi_event_dto.Response)
        event_log: Event[APIEvent] = Event(
            Core=core_dto,
            Event=APIEvent(
                Method=self._method(asgi_event_dto.Request),
                RoutePathTemplate=routes.RoutePathTemplate,
                RouteName=routes.RouteName,
                RequestPath=routes.RequestPath,
                PathParams=self._path_params(asgi_event_dto.Request),
                Status=status,
                DurationMs=asgi_event_dto.DurationMS,
                RequestSize=int(
                    asgi_event_dto.Request.headers.get("content-length") or 0
                ),
                ResponseSize=int(
                    asgi_event_dto.Response.headers.get("content-length") or 0
                ),
            ),
        )
        return event_log

    @staticmethod
    def transaction_id(request: Request) -> UUID:
        """Help main with getting a transaction ID from Request Object"""
        x_id = request.headers.get("x-request-id")
        return UUID(x_id, version=4) if x_id else request.app.state.config_log.UUID4()
