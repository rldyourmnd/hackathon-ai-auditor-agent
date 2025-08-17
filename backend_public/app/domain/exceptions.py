from __future__ import annotations


class DomainError(Exception):
    """Base domain error."""


class NotFoundError(DomainError):
    """Entity not found."""


class ValidationDomainError(DomainError):
    """Domain validation failed."""


class PipelineDomainError(DomainError):
    """Higher-level error representing pipeline-related failures from domain POV."""
