from static_paths import resolve_frontend_file


def test_frontend_asset_is_resolved(tmp_path):
    root = tmp_path / "build"
    root.mkdir()
    asset = root / "asset.js"
    asset.write_text("/* test asset */")
    assert resolve_frontend_file(root, "asset.js") == asset


def test_sibling_directory_with_same_prefix_is_rejected(tmp_path):
    root = tmp_path / "build"
    root.mkdir()
    sibling = tmp_path / "build-private"
    sibling.mkdir()
    (sibling / "private.txt").write_text("test sentinel")
    assert resolve_frontend_file(root, "../build-private/private.txt") is None


def test_absolute_outside_path_is_rejected(tmp_path):
    root = tmp_path / "build"
    root.mkdir()
    other = tmp_path / "private.txt"
    other.write_text("test sentinel")
    assert resolve_frontend_file(root, str(other)) is None


def test_symlink_outside_root_is_rejected(tmp_path):
    root = tmp_path / "build"
    root.mkdir()
    other = tmp_path / "private.txt"
    other.write_text("test sentinel")
    (root / "asset.js").symlink_to(other)
    assert resolve_frontend_file(root, "asset.js") is None


def test_missing_file_and_directory_preserve_spa_fallback(tmp_path):
    assert resolve_frontend_file(tmp_path, "calculator") is None
    assert resolve_frontend_file(tmp_path, "") is None
