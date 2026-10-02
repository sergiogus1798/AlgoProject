#!/usr/bin/env python3
"""The command: prints the board's one page and writes it as board.json and board.txt."""

from studies.research.board import inputs, many, page, store


def main() -> None:
    """Order the passing cells, print the page, leave it for the window."""
    board = many.run(inputs.scores(), inputs.memory(), inputs.CONFIG, inputs.sweep())
    text = page.text(board)
    out = store.board_dir()
    store.write(out / "board.json", board)
    (out / "board.txt").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
