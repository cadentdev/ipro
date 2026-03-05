"""Unit tests for command chaining helper functions."""
import pytest
from ipro import split_chain, _create_parser


class TestSplitChain:
    """Tests for the split_chain() function that splits argv at '+' separators."""

    def test_no_chain_single_command(self):
        """A single command with no '+' returns one segment."""
        argv = ['resize', 'photo.jpg', '--width', '300']
        result = split_chain(argv)
        assert result == [['resize', 'photo.jpg', '--width', '300']]

    def test_two_commands(self):
        """Two commands separated by '+' returns two segments."""
        argv = ['resize', 'photo.jpg', '--width', '300', '+', 'convert', '--format', 'webp']
        result = split_chain(argv)
        assert result == [
            ['resize', 'photo.jpg', '--width', '300'],
            ['convert', '--format', 'webp'],
        ]

    def test_three_commands(self):
        """Three commands separated by '+' returns three segments."""
        argv = ['resize', 'photo.jpg', '--width', '300', '+', 'convert', '--format', 'png', '+', 'rename', '--ext']
        result = split_chain(argv)
        assert result == [
            ['resize', 'photo.jpg', '--width', '300'],
            ['convert', '--format', 'png'],
            ['rename', '--ext'],
        ]

    def test_empty_argv(self):
        """Empty argv returns empty list."""
        result = split_chain([])
        assert result == []

    def test_only_plus(self):
        """A single '+' with no commands returns empty list."""
        result = split_chain(['+'])
        assert result == []

    def test_leading_plus(self):
        """Leading '+' is ignored (empty first segment skipped)."""
        argv = ['+', 'convert', '--format', 'webp']
        result = split_chain(argv)
        assert result == [['convert', '--format', 'webp']]

    def test_trailing_plus(self):
        """Trailing '+' is ignored (empty trailing segment skipped)."""
        argv = ['resize', 'photo.jpg', '--width', '300', '+']
        result = split_chain(argv)
        assert result == [['resize', 'photo.jpg', '--width', '300']]

    def test_consecutive_plus(self):
        """Consecutive '+' signs produce no empty segments."""
        argv = ['resize', 'photo.jpg', '+', '+', 'convert', '--format', 'webp']
        result = split_chain(argv)
        assert result == [
            ['resize', 'photo.jpg'],
            ['convert', '--format', 'webp'],
        ]

    def test_preserves_argument_order(self):
        """Arguments within each segment maintain their order."""
        argv = ['convert', 'img.jpg', '--format', 'png', '--quality', '80', '--strip-exif',
                '+', 'resize', '--width', '100,200']
        result = split_chain(argv)
        assert result == [
            ['convert', 'img.jpg', '--format', 'png', '--quality', '80', '--strip-exif'],
            ['resize', '--width', '100,200'],
        ]

    def test_plus_in_filename_not_split(self):
        """'+' is only treated as separator when it's its own token.
        Filenames containing '+' are not split (they appear as part of a larger token)."""
        # A filename like "photo+extra.jpg" is a single token, not split
        argv = ['info', 'photo+extra.jpg']
        result = split_chain(argv)
        assert result == [['info', 'photo+extra.jpg']]


class TestCreateParser:
    """Tests for the _create_parser() function."""

    def test_returns_parser(self):
        """_create_parser returns an ArgumentParser."""
        import argparse
        parser = _create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_has_info_command(self):
        """Parser supports the 'info' subcommand."""
        parser = _create_parser()
        args = parser.parse_args(['info', 'photo.jpg'])
        assert args.command == 'info'

    def test_parser_has_resize_command(self):
        """Parser supports the 'resize' subcommand."""
        parser = _create_parser()
        args = parser.parse_args(['resize', 'photo.jpg', '--width', '300'])
        assert args.command == 'resize'

    def test_parser_has_convert_command(self):
        """Parser supports the 'convert' subcommand."""
        parser = _create_parser()
        args = parser.parse_args(['convert', 'photo.jpg', '--format', 'webp'])
        assert args.command == 'convert'

    def test_parser_has_rename_command(self):
        """Parser supports the 'rename' subcommand."""
        parser = _create_parser()
        args = parser.parse_args(['rename', 'photo.jpg', '--ext'])
        assert args.command == 'rename'

    def test_parser_has_func_attribute(self):
        """Parsed args include the func attribute for command dispatch."""
        parser = _create_parser()
        args = parser.parse_args(['info', 'photo.jpg'])
        assert hasattr(args, 'func')
        assert callable(args.func)
