"""gRPC MemberService servicer — thin adapter over MemberService."""

from __future__ import annotations

import uuid

from library.adapter.db.repositories.member_repo import SqlAlchemyMemberRepository
from library.controller.grpc.base import AuthenticatedServicer
from library.controller.grpc.errors import grpc_status_for
from library.core.commands import MemberCreate
from library.core.entities import Member
from library.core.errors import DomainError, ValidationError
from library.service.member_service import MemberService
from library.v1 import common_pb2, members_pb2, members_pb2_grpc


def _member_proto(m: Member) -> members_pb2.Member:
    return members_pb2.Member(
        id=str(m.id),
        first_name=m.first_name,
        last_name=m.last_name,
        email=m.email,
        phone=m.phone or "",
        address=m.address or "",
        status=m.status.value,
    )


def _parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValidationError("id must be a valid UUID") from exc


class MemberServicer(AuthenticatedServicer, members_pb2_grpc.MemberServiceServicer):
    def _svc(self, session) -> MemberService:
        return MemberService(SqlAlchemyMemberRepository(session))

    async def CreateMember(self, request, context) -> members_pb2.Member:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            try:
                member = await self._svc(session).create_member(
                    MemberCreate(
                        first_name=request.first_name,
                        last_name=request.last_name,
                        email=request.email,
                        phone=request.phone or None,
                        address=request.address or None,
                    )
                )
                await session.commit()
                return _member_proto(member)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def UpdateMember(self, request, context) -> members_pb2.Member:
        await self._authenticate(context)
        changes: dict = {}
        for field in ("first_name", "last_name", "email", "phone", "address", "status"):
            value = getattr(request, field)
            if value:
                changes[field] = value
        async with self._sessionmaker() as session:
            try:
                member = await self._svc(session).update_member(
                    _parse_uuid(request.id), changes
                )
                await session.commit()
                return _member_proto(member)
            except DomainError as exc:
                await session.rollback()
                await context.abort(grpc_status_for(exc), exc.message)

    async def GetMember(self, request, context) -> members_pb2.Member:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            try:
                member = await self._svc(session).get_member(_parse_uuid(request.id))
                return _member_proto(member)
            except DomainError as exc:
                await context.abort(grpc_status_for(exc), exc.message)

    async def ListMembers(self, request, context) -> members_pb2.ListMembersResponse:
        await self._authenticate(context)
        async with self._sessionmaker() as session:
            members, total = await self._svc(session).list_members(
                request.search or None, request.page.limit or None, request.page.offset
            )
            return members_pb2.ListMembersResponse(
                members=[_member_proto(m) for m in members],
                page=common_pb2.PageInfo(
                    limit=request.page.limit or 20, offset=request.page.offset, total=total
                ),
            )
