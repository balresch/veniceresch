"""Base class for every Pydantic model in this SDK.

Applied to generated types via ``datamodel-codegen --base-class ...`` (see
``scripts/regen_types.sh``) and to hand-written response shapes in
``types.py``. The single shared setting is ``extra="allow"``: Venice adds
fields to its responses regularly, and silently accepting them keeps this
SDK from breaking at every new field rollout.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VeniceBaseModel(BaseModel):
    """Shared base for every Venice Pydantic model.

    - ``extra="allow"``: unknown fields are preserved on the instance
      instead of raising. Venice's OpenAPI spec often lags the wire format
      by days or weeks; ignoring new fields would turn every new server
      feature into a client-side validation error.
    """

    model_config = ConfigDict(extra="allow")


__all__ = ["VeniceBaseModel"]
