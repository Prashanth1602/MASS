from pathlib import Path

from app.database_generator import DatabaseGenerator


def test_generates_shared_database_module(tmp_path: Path):
    generated_files = DatabaseGenerator().generate(tmp_path)

    database_file = tmp_path / "app" / "core" / "database.py"
    init_file = tmp_path / "app" / "core" / "__init__.py"

    assert database_file.is_file()
    assert init_file.is_file()
    assert str(database_file) in generated_files
    assert str(init_file) in generated_files

    content = database_file.read_text(encoding="utf-8")

    assert "database_url" in content
    assert "create_engine" in content
    assert "SessionLocal" in content
    assert "declarative_base" in content
    assert "def get_db()" in content
