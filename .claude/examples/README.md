# Perfect Implementation Examples

This directory contains **perfect reference implementations** for Claude Code to learn from.

**How to use these:**
1. Always point Claude Code to the relevant example before starting implementation
2. Say: "Follow the EXACT pattern in .claude/examples/perfect_{type}.py"
3. Claude will copy the structure and adapt for your use case

---

## 📄 Available Examples

### perfect_entity.py
**What:** Domain entity (Review) with full business logic
**Use for:** Creating new entities (Widget, Merchant, Order, etc.)

**Example prompt:**
```
Create Widget entity following .claude/examples/perfect_entity.py

Same structure:
- @dataclass
- Enums for types
- validate() method
- Business logic methods
```

### perfect_repository_interface.py
**What:** Repository interface (IReviewRepository) with all operations
**Use for:** Creating repository interfaces

### perfect_repository_implementation.py
**What:** PostgreSQL repository implementation
**Use for:** Implementing repository interfaces

### perfect_service.py
**What:** Service with business logic (ReviewService)
**Use for:** Creating domain services

### perfect_route.py
**What:** FastAPI routes (review endpoints)
**Use for:** Creating API routes

### perfect_test.py
**What:** Comprehensive test file
**Use for:** Creating test files

---

## 🚀 Quick Reference

### Creating New Feature

**Step 1: Entity**
```
Create {Name} entity following .claude/examples/perfect_entity.py
```

**Step 2: Repository Interface**
```
Create I{Name}Repository following .claude/examples/perfect_repository_interface.py
```

**Step 3: Repository Implementation**
```
Create Postgres{Name}Repository following .claude/examples/perfect_repository_implementation.py
```

**Step 4: Service**
```
Create {Name}Service following .claude/examples/perfect_service.py
```

**Step 5: Routes**
```
Create {name} routes following .claude/examples/perfect_route.py
```

**Step 6: Tests**
```
Create tests following .claude/examples/perfect_test.py
```

---

**Remember:** These examples are the source of truth. When in doubt, copy them exactly!
