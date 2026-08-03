from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.sessions import (
    ConfirmationRequest,
    LocationRequest,
    SessionFinishRequest,
    SessionRequest,
)
from app.services.container import work_session_service
from app.services.work_sessions import SessionConflict, SessionError, SessionNotFound

router = APIRouter(prefix="/api")


def _http_error(exc: SessionError) -> HTTPException:
    if isinstance(exc, SessionNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, SessionConflict):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/catalog")
def catalog() -> dict[str, object]:
    return work_session_service.catalog()


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def start_session(request: SessionRequest) -> dict[str, object]:
    try:
        return work_session_service.start(request)
    except SessionError as exc:
        raise _http_error(exc) from exc

@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict[str, object]:
    try:
        return work_session_service.get(session_id)
    except SessionError as exc:
        raise _http_error(exc) from exc


@router.post("/sessions/{session_id}/locations", status_code=status.HTTP_201_CREATED)
def add_location(session_id: str, request: LocationRequest) -> dict[str, object]:
    try:
        return work_session_service.add_location(session_id, request)
    except SessionError as exc:
        raise _http_error(exc) from exc


@router.post("/sessions/{session_id}/finish")
async def finish_session(
    session_id: str,
    request: SessionFinishRequest,
) -> dict[str, object]:
    try:
        return await work_session_service.finish(session_id, request.end_time)
    except SessionError as exc:
        raise _http_error(exc) from exc


@router.get("/sessions/{session_id}/event")
def get_event(session_id: str) -> dict[str, object]:
    try:
        return work_session_service.get_event(session_id)
    except SessionError as exc:
        raise _http_error(exc) from exc


@router.get("/sessions/{session_id}/export.json")
def export_json(session_id: str) -> Response:
    try:
        content = work_session_service.export_json(session_id)
    except SessionError as exc:
        raise _http_error(exc) from exc
    filename = quote(f"nongsi-{session_id}.json")
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.get("/sessions/{session_id}/export.csv")
def export_csv(session_id: str) -> Response:
    try:
        content = work_session_service.export_csv(session_id)
    except SessionError as exc:
        raise _http_error(exc) from exc
    filename = quote(f"nongsi-{session_id}.csv")
    return Response(
        content="\ufeff" + content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.post("/events/{event_id}/confirm")
def confirm_event(
    event_id: str,
    request: ConfirmationRequest,
) -> dict[str, object]:
    try:
        return work_session_service.confirm(event_id, request)
    except SessionError as exc:
        raise _http_error(exc) from exc
