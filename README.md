# t-alpha

AmazingData-backed market API and T+0 alert service.

## Local setup

1. Create `.env` from `.env.example`.
2. Put real AmazingData and MySQL credentials in `.env`.
3. Install dependencies:

```powershell
python -m pip install -e ".[dev]"
```

4. Run tests:

```powershell
pytest -q
```

5. Start API:

```powershell
uvicorn t_alpha.main:app --reload
```

Credentials must not be committed.
