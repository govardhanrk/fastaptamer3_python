# Run Backend Script
Set-Location "d:\Academic\Labwork\Repositories\fastaptameR3-python\fastaptamer3_python\backend"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
