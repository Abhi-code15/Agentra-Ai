# ADR-003: Standardize on SQLAlchemy 2.0 Declarative Syntax

**Status:** Accepted  
**Date:** 2026-11-12  
**Deciders:** Backend Lead, Software Architect  

---

## 1. Context
SQLAlchemy 1.4 allowed legacy querying patterns (`session.query(Model)`) that lacked static typing support, caused implicit query loading bugs, and differed fundamentally from the clean typing idioms of modern Python 3.10+.

## 2. Decision
Adopt strict **SQLAlchemy 2.0 Declarative Mappings** using `Mapped[...]` and `mapped_column(...)`, and execute queries exclusively via `select(...)` statements (`db.execute(select(Model).where(...))`).

## 3. Alternatives Considered
- **SQLAlchemy 1.4 Legacy Syntax:** Rejected because it will be deprecated, lacks native IDE autocompletion with mypy, and promotes bad transactional habits.
- **SQLModel / Tortoise ORM / Peewee:** Rejected to maintain standard enterprise Python ecosystem compatibility and first-class Alembic autogeneration support.

## 4. Consequences
- **Positive:** Type-safety throughout models and repositories, explicit query syntax, clear error messages, modern developer experience for engineers learning FastAPI.
- **Trade-offs:** Slightly more verbose model class definitions compared to older declarative bases.
