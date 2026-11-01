"""Interactive prompt when no Target is given (ticket 12)."""

from __future__ import annotations

import sample_set


def test_prompts_for_a_target_and_converts_it(run, tmp_path):
    source = sample_set.build_csv(tmp_path)

    result = run(stdin=f"{source}\n")

    assert "File or folder to convert:" in result.output
    assert result.exit_code == 0
    assert (tmp_path / "sales.md").exists()


def test_accepts_a_quoted_path(run, tmp_path):
    folder = tmp_path / "My Documents"
    folder.mkdir()
    source = sample_set.build_csv(folder)

    run(stdin=f'"{source}"\n')

    assert (folder / "sales.md").exists()


def test_accepts_a_path_with_backslash_escaped_spaces(run, tmp_path):
    """macOS Terminal escapes spaces when a file is dragged into the window."""
    folder = tmp_path / "My Documents"
    folder.mkdir()
    sample_set.build_csv(folder)
    escaped = str(folder / "sales.csv").replace("My Documents", "My\\ Documents")

    run(stdin=f"{escaped}\n")

    assert (folder / "sales.md").exists()


def test_asks_again_when_the_path_does_not_exist(run, tmp_path):
    source = sample_set.build_csv(tmp_path)

    result = run(stdin=f"{tmp_path / 'nope.csv'}\n{source}\n")

    assert "does not exist" in result.output
    assert result.output.count("File or folder to convert:") == 2
    assert (tmp_path / "sales.md").exists()


def test_prompted_folder_shows_count_and_asks_to_confirm(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    result = run(stdin=f"{library}\n\n")

    assert "Found 4 supported files, convert? [Y/n]" in result.output
    assert (library / "sales.md").exists()


def test_answering_no_converts_nothing(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    result = run(stdin=f"{library}\nn\n")

    assert result.exit_code == 0
    assert not (library / "sales.md").exists()
    assert "Nothing was converted." in result.output


def test_folder_given_as_an_argument_is_not_confirmed(run, tmp_path):
    library = sample_set.build_folder_tree(tmp_path)

    result = run(library)

    assert "convert? [Y/n]" not in result.output
    assert (library / "sales.md").exists()


def test_end_of_input_at_the_prompt_is_invalid_usage(run):
    result = run(stdin="")

    assert result.exit_code == 2
