# Claude Code Workflow Guide
## How to Get Maximum Velocity from AI-Assisted Development

---

## The Golden Prompt Template

**Use this structure for EVERY task:**

```
CONTEXT: [What Claude needs to understand]
├─ Read: [Specific files to analyze]
├─ Understand: [Key patterns to follow]
└─ Reference: [Similar existing code]

TASK: [What to build]
├─ Create: [Files to create]
├─ Update: [Files to modify]
└─ Follow: [Specific patterns]

REQUIREMENTS: [Non-negotiable criteria]
├─ Tests first (TDD)
├─ Type hints everywhere
├─ Docstrings for public methods
├─ Follow existing patterns EXACTLY
└─ 100% test coverage

OUTPUT: [What success looks like]
├─ All tests pass
├─ No linting errors
├─ Follows PATTERNS.md
└─ Ready for review
```

---

## Workflow Steps

### Step 1: Point to Examples (Critical!)

**❌ Bad:**
```
"Create a review repository"
```

**✅ Good:**
```
CONTEXT: Read .claude/examples/perfect_repository_implementation.py

TASK: Create postgres_widget_repository.py following the EXACT same pattern

REQUIREMENTS:
- Same structure as ReviewRepository
- Same error handling
- Same mapper pattern
- Tests mirror test_review_repository.py
```

**Why:** Claude learns from examples 10x faster than from descriptions.

---

## Quick Reference

### Pattern 1: "Create similar to X"
```
Create {new_thing} following the EXACT pattern of {existing_thing}
1. Copy structure from {file_path}
2. Adapt for {new_use_case}
3. Keep same error handling
4. Mirror test structure
```

### Pattern 2: "Add feature to existing"
```
CONTEXT: Read {existing_file}

TASK: Add {new_method} to {existing_class}

REQUIREMENTS:
- Follow existing method patterns in the file
- Add tests in {test_file}
- Update existing tests if needed
```

---

## Pro Tips

### 1. Always Provide File Paths
**❌ Bad:** "Update the review service"
**✅ Good:** "Update services/review_service/domain/services/review_service.py"

### 2. Reference Line Numbers
**❌ Bad:** "Fix the bug"
**✅ Good:** "Fix lines 45-50 in review_service.py"

### 3. Show Examples
**❌ Bad:** "Add error handling"
**✅ Good:** "Add error handling like lines 89-95 in review_service.py"

---

**Remember:** Claude Code is an assistant, not a replacement. Together = 10x velocity 🚀
