# 🎯 NeoBank — Interview Cheat Sheet

> Everything you need to **confidently explain this project** in your TCS Python interview. Read this until you can talk about each section naturally, in your own words. Don't memorise word-for-word — understand it.

---

## 1) Your 30-second pitch (say this when asked "tell me about your Python project")

> *"I built NeoBank, a production-style bank management system in pure Python. It's fully object-oriented and uses a layered architecture — domain models, a service layer for business logic, and a repository layer for storage — so the parts are decoupled and testable. It has **two front-ends over the same engine: a modern Tkinter desktop GUI and a command-line interface**. It supports accounts, deposits, withdrawals, and atomic money transfers with rollback. PINs are securely hashed, all data persists to JSON with crash-safe writes, and I wrote 18 unit tests covering the edge cases. I deliberately used only the standard library to show strong core Python."*

> 🎤 **Killer line to drop in:** *"The fact that a GUI and a CLI both run the exact same `BankService` without any duplicated logic is what proves the architecture is clean — the business rules live in one place only."*

---

## 2) Why these design choices? (the "senior" answers)

| If they ask… | Say… |
|---|---|
| **Why layers / why not one file?** | "Separation of concerns. The CLI handles I/O, the service holds business rules, the repository handles storage. Each layer is independently testable and replaceable." |
| **Why the Repository pattern?** | "So the business logic never depends on the storage format. I can switch from JSON to SQLite by writing a new repository class — the service layer doesn't change at all." |
| **Why custom exceptions?** | "They make the code self-documenting and let callers catch errors at the right level — e.g. `InsufficientFundsError` vs a generic `Exception`." |
| **Why hash the PIN?** | "You must never store credentials in plaintext. I use salted PBKDF2-HMAC-SHA256 with a constant-time comparison to resist brute-force and timing attacks." |
| **Why atomic writes?** | "If the program crashes mid-write, a partial file would corrupt all data. I write to a temp file then `os.replace` it, which is atomic on the OS level." |
| **What's the transfer rollback?** | "A transfer is two steps: debit source, credit target. If the credit fails, I reverse the debit with a compensating transaction so money is never lost." |
| **Why both a GUI and a CLI?** | "To prove the architecture. Both are just presentation layers calling `BankService`. The same engine drives both — zero duplicated business logic." |
| **How did you build the GUI?** | "Pure Tkinter, no UI libraries. I built a small design system in `theme.py` — rounded cards drawn on a Canvas, a colour palette, hover-animated buttons — then composed the screens in `app.py`." |
| **Why didn't you use a UI framework?** | "To showcase core Python and Tkinter fundamentals. It also keeps the project dependency-free, so it runs anywhere Python is installed." |

---

## 3) Core Python concepts → where you used them (THIS is the gold)

Be ready to point to a concept and say where it lives in your code:

- **Classes & objects / `__init__` / `self`** → `Account`, `Transaction`, `BankService` in `models.py`, `services.py`
- **Encapsulation** → balance only changes through `deposit()`/`withdraw()`; PIN hidden behind `verify_pin()`
- **Inheritance** → `AccountType(str, Enum)`, `AccountRepository(ABC)`, custom exceptions extend `BankError`
- **Polymorphism** → `JsonAccountRepository` and `InMemoryAccountRepository` are used interchangeably through the same interface
- **Abstraction** → `AccountRepository` is an abstract base class (`@abstractmethod`)
- **Dataclasses** → `@dataclass` on `Account` and `@dataclass(frozen=True)` on `Transaction` (immutable audit record)
- **Properties** → `available_balance`, `overdraft_limit`, `annual_interest_rate`
- **Dunder methods** → `__str__` for friendly printing
- **Enums** → type-safe categories instead of magic strings
- **Exception handling** → `try/except/finally`, custom hierarchy, `raise`
- **File handling** → reading/writing JSON in `repository.py`
- **Modules & packages** → the `banksystem/` package with `__init__.py`
- **Comprehensions, f-strings, type hints** → throughout
- **GUI / event-driven programming** → `gui/app.py` (Tkinter widgets, event bindings, callbacks); `gui/theme.py` (custom reusable `Card`, `Button`, `Field` widgets)

---

## 4) The HONEST framing (very important)

You chose Python as your TCS skill but your deployed projects are MERN. Use this exact honesty:

> *"My deployed full-stack projects are in the MERN stack, which is where I built my product experience. I chose Python as my skill, and to back that up I built NeoBank — a complete object-oriented Python project — so I could apply Python fundamentals and OOP in a real, working system rather than just theory."*

✅ Honest. ✅ Shows initiative. ✅ Turns your only "gap" into a strength.

---

## 5) Likely follow-up coding questions (and quick answers)

- **"Show me a class from your project."** → Draw `Account` with `__init__`, an attribute, and a `deposit` method.
- **"What is `self`?"** → "A reference to the current object instance; Python passes it automatically."
- **"Difference between your two repositories?"** → "Same interface, different storage — one in a dict, one in a JSON file. That's polymorphism via an abstract base class."
- **"What's mutable vs immutable here?"** → "`Account` is mutable (balance changes); `Transaction` is `frozen=True`, immutable, because an audit record must never change."
- **"How would you scale it?"** → "Swap the repository for SQLite/Postgres, then add a FastAPI layer on top of `BankService`."
- **"Time complexity of looking up an account?"** → "O(1) — accounts are keyed by account number in a dict."

---

## 6) 60-second live walkthrough (if they ask you to run it)

```bash
python app.py           # the modern desktop GUI (most impressive — show this!)
python demo.py          # shows the whole system working, no typing
python -m unittest discover -s tests -v   # shows 18 tests passing
python main.py          # terminal version: open account → deposit → transfer
```

**If you show the GUI:** register an account, deposit, transfer, then open the
Statement tab. Narrate: *"Notice the GUI never does any maths — every button
calls a method on `BankService`, the same engine the CLI uses."*

**If you show the demo/CLI:** *"Here it opens two accounts, does a transfer,
blocks an invalid withdrawal, applies interest, and prints a statement — all
going through the service layer."*

---

## 7) One-line summaries to memorise

- **What is it?** "An OOP bank management system in pure Python with a layered, testable architecture."
- **Hardest part?** "Getting the atomic transfer with rollback right so money can never be lost."
- **Proudest part?** "Secure PIN hashing and a clean repository pattern — it feels production-ready, not like a student script."
- **What did you learn?** "How to structure a real Python project: separating concerns, writing tests, and handling errors properly."

---

### ✅ Final tip
Speak calmly, point to concepts in *your own* code, and admit honestly when you don't know something — then say how you'd find out. That confidence + honesty is exactly what TCS wants in a fresher. **You've got this, Brijesh!**
