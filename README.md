# 🏦 NeoBank — Production-Grade Bank Management System

> A clean, layered, fully object-oriented banking application written in **pure Python** (standard library only — zero runtime dependencies). It ships with **two front-ends over one engine**: a modern, dark-themed **Tkinter desktop GUI** and an interactive **command-line interface**. Built to demonstrate professional software-engineering practices end to end: domain modelling, custom exceptions, the repository pattern, a service layer, secure credential handling, structured logging, and a comprehensive automated test suite.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![GUI](https://img.shields.io/badge/GUI-Tkinter-9B59B6)
![Tests](https://img.shields.io/badge/tests-18%20passing-brightgreen)
![Dependencies](https://img.shields.io/badge/runtime%20deps-none-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

> 💡 **Architecture highlight:** the GUI and the CLI are *both* thin presentation layers over the same `BankService`. Neither contains business logic. This is a textbook demonstration of separation of concerns — you can drive the exact same banking engine from a window or a terminal.

---

## 🖥️ Desktop GUI (Tkinter)

A modern, dark-themed banking dashboard built **from scratch** with Tkinter — custom rounded cards, a gradient brand panel, sidebar navigation, hover-animated buttons, toast notifications and a colour-coded statement table. No third-party UI libraries.

| Screen | Highlights |
|---|---|
| **Login / Register** | Split-screen layout with a gradient brand panel; masked PIN entry |
| **Overview** | Gradient balance card, in/out/transaction stat cards, quick-action buttons |
| **Deposit / Withdraw / Transfer** | Clean card-based forms with instant feedback toasts |
| **Statement** | Styled table with green inflows / red outflows |
| **Settings** | Change PIN, close account (with a clear danger zone) |

> Run it with `python app.py`. (A terminal version is also available — see below.)

---

## ✨ Features

| Category | What it does |
|---|---|
| **Two interfaces** | Modern **Tkinter GUI** (`app.py`) *and* an interactive **CLI** (`main.py`) |
| **Accounts** | Open `SAVINGS` / `CURRENT` accounts, auto-generated account numbers, close accounts |
| **Transactions** | Deposit, withdraw, **atomic transfers with automatic rollback** |
| **Business rules** | `SAVINGS` cannot overdraw; `CURRENT` has an overdraft limit; per-product interest |
| **Security** | PINs stored only as **salted PBKDF2-HMAC-SHA256 hashes**; constant-time verification; hidden PIN entry |
| **Persistence** | JSON storage via the **Repository pattern** with **atomic, crash-safe writes** |
| **Auditing** | Immutable transaction ledger + a structured `bank.log` audit trail |
| **Interest engine** | Batch job that credits interest to all active accounts |
| **CLI** | Friendly, menu-driven interface that never crashes on bad input |
| **Quality** | 18 unit tests covering happy paths **and** edge cases |

---

## 🏛️ Architecture

This project is deliberately **layered** so each part has a single responsibility and the layers are easy to test and swap. The CLI depends on the service, the service depends on a repository *interface* — not on any concrete storage format.

```
┌─────────────────────────────────────────────────────────┐
│  gui/  +  cli.py   Presentation layer (window / terminal)│
├─────────────────────────────────────────────────────────┤
│  services.py       Business logic  (BankService facade)  │
├─────────────────────────────────────────────────────────┤
│  repository.py     Persistence  (Repository pattern)     │
│                      • JsonAccountRepository (durable)    │
│                      • InMemoryAccountRepository (tests)  │
├─────────────────────────────────────────────────────────┤
│  models.py         Domain entities (Account, Transaction)│
│  security.py       Password/PIN hashing                  │
│  exceptions.py     Custom exception hierarchy            │
│  utils.py          Logging, validation, formatting       │
└─────────────────────────────────────────────────────────┘
```

```
bank-management-system/
├── banksystem/
│   ├── __init__.py        # package API
│   ├── models.py          # Account, Transaction, enums (OOP core)
│   ├── exceptions.py      # custom exception tree
│   ├── security.py        # salted PBKDF2 PIN hashing
│   ├── repository.py      # abstract + JSON + in-memory repositories
│   ├── services.py        # BankService (business logic)
│   ├── cli.py             # interactive command-line interface
│   ├── utils.py           # logging, validation, table rendering
│   └── gui/               # modern Tkinter desktop interface
│       ├── __init__.py
│       ├── theme.py       # design system: colours, fonts, widgets
│       └── app.py         # screens + navigation (NeoBankApp)
├── tests/
│   └── test_bank.py       # 18 unit tests (unittest / pytest)
├── data/                  # runtime data + logs (git-ignored)
├── app.py                 # GUI entry point   ->  python app.py
├── main.py                # CLI entry point   ->  python main.py
├── demo.py                # scripted, non-interactive walkthrough
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

> Requires **Python 3.10+**. No installation or third-party packages needed.

```bash
# 1. Clone your repository
git clone https://github.com/brijeshrakholiya17/bank-management-system.git
cd bank-management-system

# 2a. Launch the modern desktop GUI  (recommended)
python app.py

# 2b. ...or run the interactive terminal app
python main.py

# 3. (Optional) Watch the scripted demo — no typing required
python demo.py

# 4. Run the test suite
python -m unittest discover -s tests -v
#   or, if you have pytest installed:
pytest -q
```

> **Note:** Tkinter ships with Python on Windows and macOS. On some Linux
> distros install it once with `sudo apt install python3-tk`.

---

## 🧪 Tests

The suite uses an **in-memory repository** so it is fast and leaves no files behind. It verifies the happy paths *and* the tricky edge cases that real banking code must handle:

- ✅ PINs are hashed, salted, and never stored in plaintext
- ✅ Negative / zero amounts are rejected
- ✅ `SAVINGS` accounts cannot overdraw; `CURRENT` overdraft works within its limit
- ✅ Wrong PIN and unknown account raise the correct exceptions
- ✅ **Transfer rolls back** if the credit leg fails (money is never lost)
- ✅ Closed/frozen accounts reject all operations
- ✅ Serialization round-trips correctly

```
Ran 18 tests in 1.7s — OK
```

---

## 🔐 A Note on Security

Customer PINs are **never** stored or logged in plaintext. Each PIN is salted with 16 random bytes and hashed using **PBKDF2-HMAC-SHA256** (200,000 iterations). Verification uses a **constant-time comparison** to resist timing attacks. This mirrors how production systems handle credentials.

---

## 🧠 Engineering Concepts Demonstrated

- **OOP:** encapsulation, inheritance (`Enum`/`ABC`), polymorphism, abstraction, dataclasses, dunder methods, properties
- **Design patterns:** Repository pattern, Service/Facade layer, Dependency Injection
- **GUI engineering:** a custom Tkinter design system (rounded canvas cards, gradients, hover states, toasts) built without any UI framework
- **Robustness:** custom exception hierarchy, input validation, atomic file writes, transaction rollback
- **Best practices:** type hints throughout, logging, separation of concerns, unit testing, zero global state

---

## 🗺️ Possible Extensions

- Swap the JSON repository for **SQLite** (only `repository.py` changes)
- Add a **Flask/FastAPI** REST layer on top of `BankService`
- Add scheduled interest accrual and monthly statements (PDF/email)

---

## 📄 License

Released under the **MIT License**.

---

**Author:** Brijesh Rakholiya · [GitHub](https://github.com/brijeshrakholiya17) · [LinkedIn](https://linkedin.com/in/brijeshrakholiya17)
