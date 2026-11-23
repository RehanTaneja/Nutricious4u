"""Request authentication and authorization for the API.

Callers identify themselves with a Firebase ID token:
    Authorization: Bearer <token>
(or ?token=<token> on routes that opt in, e.g. URLs opened directly in a PDF viewer).

Rollout is phased via the AUTH_ENFORCE environment variable:
  - AUTH_ENFORCE unset/false: requests WITHOUT a token are still allowed (and logged),
    so app versions that predate token support keep working. Requests WITH a token
    are always verified and authorized.
  - AUTH_ENFORCE=true: every protected route requires a valid token.
An invalid or expired token is always rejected (401), in both modes.

The dietician is identified by isDietician on the caller's user_profiles document.
"""
import asyncio
import logging
import os
import time
from typing import Callable, Optional

from fastapi import HTTPException, Request
from firebase_admin import auth as fb_auth

logger = logging.getLogger(__name__)

DIETICIAN_EMAIL = "nutricious4u@gmail.com"

# Fields only the dietician or the backend itself may change on a user profile.
PROTECTED_PROFILE_FIELDS = (
    "isDietician",
    "subscriptionPlan", "subscriptionStartDate", "subscriptionEndDate",
    "currentSubscriptionAmount", "totalAmountPaid", "isSubscriptionActive",
    "autoRenewalEnabled", "freeTrialUsed", "freeTrialStartDate", "freeTrialEndDate",
    "pendingPlanSwitch", "nextPlanId", "subscriptionStatus", "lastPaymentReminderSent",
    "dietPdfUrl", "lastDietUpload", "dieticianId", "dietCacheVersion",
    "isAppLocked",
)

_db_getter: Callable[[], object] = lambda: None
_dietician_cache: dict = {}
_DIETICIAN_CACHE_TTL = 60.0


def configure(db_getter: Callable[[], object]) -> None:
    """Give the guard access to the Firestore client (lazily, it may be None at import)."""
    global _db_getter
    _db_getter = db_getter


def enforcing() -> bool:
    return os.environ.get("AUTH_ENFORCE", "false").strip().lower() in ("1", "true", "yes", "on")


class Caller:
    def __init__(self, uid: str, email: Optional[str], email_verified: bool):
        self.uid = uid
        self.email = email
        self.email_verified = email_verified

    @property
    def has_dietician_email(self) -> bool:
        return bool(self.email_verified and self.email and self.email.lower() == DIETICIAN_EMAIL)


def _extract_token(request: Request, allow_query_token: bool) -> Optional[str]:
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        token = header[7:].strip()
        if token:
            return token
    if allow_query_token:
        token = request.query_params.get("token")
        if token:
            return token
    return None


async def get_caller(request: Request, allow_query_token: bool = False) -> Optional[Caller]:
    """Verify the caller's token. Returns None only for token-less requests while not enforcing."""
    if hasattr(request.state, "caller_resolved"):
        return request.state.caller
    token = _extract_token(request, allow_query_token)
    caller: Optional[Caller] = None
    if token is None:
        if enforcing():
            raise HTTPException(status_code=401, detail="Authentication required")
        logger.info(f"[AUTH] Unauthenticated request allowed (AUTH_ENFORCE off): {request.method} {request.url.path}")
    else:
        try:
            decoded = await asyncio.to_thread(fb_auth.verify_id_token, token)
        except Exception as e:
            logger.warning(f"[AUTH] Rejected invalid token on {request.method} {request.url.path}: {type(e).__name__}")
            raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
        caller = Caller(decoded["uid"], decoded.get("email"), bool(decoded.get("email_verified")))
    request.state.caller = caller
    request.state.caller_resolved = True
    return caller


async def is_dietician(uid: str) -> bool:
    now = time.monotonic()
    cached = _dietician_cache.get(uid)
    if cached and now - cached[1] < _DIETICIAN_CACHE_TTL:
        return cached[0]
    db = _db_getter()
    if db is None:
        raise HTTPException(status_code=503, detail="Firebase service is currently unavailable. Please try again later.")
    doc = await asyncio.to_thread(lambda: db.collection("user_profiles").document(uid).get())
    value = bool(doc.exists and (doc.to_dict() or {}).get("isDietician", False))
    _dietician_cache[uid] = (value, now)
    return value


async def caller_is_dietician(caller: Optional[Caller]) -> bool:
    return caller is not None and await is_dietician(caller.uid)


async def _body_field(request: Request, field: str) -> Optional[str]:
    try:
        body = await request.json()
    except Exception:
        return None
    if isinstance(body, dict):
        value = body.get(field)
        return str(value) if value is not None else None
    return None


# ---- dependency factories (use with dependencies=[Depends(...)]) ----

def require_login():
    async def dep(request: Request):
        await get_caller(request)
    return dep


def require_dietician():
    async def dep(request: Request):
        caller = await get_caller(request)
        if caller is None:
            return  # phased mode, token-less legacy client
        if not await is_dietician(caller.uid):
            raise HTTPException(status_code=403, detail="Dietician access required")
    return dep


def require_self_or_dietician(param: str, source: str = "path", allow_query_token: bool = False):
    """The caller must be the user named by `param` (from path/body/query) or the dietician."""
    async def dep(request: Request):
        caller = await get_caller(request, allow_query_token=allow_query_token)
        if caller is None:
            return  # phased mode, token-less legacy client
        if source == "path":
            target = request.path_params.get(param)
        elif source == "query":
            target = request.query_params.get(param)
        else:
            target = await _body_field(request, param)
        if target is not None and target == caller.uid:
            return
        if target is None and source == "query":
            # Optional query filter absent: only the dietician may list everything.
            if await is_dietician(caller.uid):
                return
            raise HTTPException(status_code=403, detail="Not allowed")
        if await is_dietician(caller.uid):
            return
        raise HTTPException(status_code=403, detail="Not allowed to access another user's data")
    return dep


def require_doc_owner_or_dietician(collection: str, id_param: str, owner_field: str = "userId"):
    """The caller must own the document (by owner_field) or be the dietician."""
    async def dep(request: Request):
        caller = await get_caller(request)
        if caller is None:
            return  # phased mode, token-less legacy client
        if await is_dietician(caller.uid):
            return
        db = _db_getter()
        if db is None:
            raise HTTPException(status_code=503, detail="Firebase service is currently unavailable. Please try again later.")
        doc_id = request.path_params.get(id_param)
        doc = await asyncio.to_thread(lambda: db.collection(collection).document(doc_id).get())
        if doc.exists and (doc.to_dict() or {}).get(owner_field) == caller.uid:
            return
        if not doc.exists:
            return  # let the route return its own not-found response
        raise HTTPException(status_code=403, detail="Not allowed")
    return dep


async def strip_protected_fields(request: Request, data: dict) -> dict:
    """Drop fields a non-dietician caller may not set. Values are ignored, not rejected,
    because the app sends the whole fetched profile back on edit."""
    caller = await get_caller(request)
    if await caller_is_dietician(caller):
        return data
    removed = [k for k in PROTECTED_PROFILE_FIELDS if k in data]
    if removed:
        logger.info(f"[AUTH] Ignoring protected profile fields from non-dietician caller: {removed}")
    return {k: v for k, v in data.items() if k not in PROTECTED_PROFILE_FIELDS}
