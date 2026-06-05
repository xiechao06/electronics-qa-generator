from electronics_qa_generator import __version__
from electronics_qa_generator.cli import build_parser


def test_version():
    assert isinstance(__version__, str)
    assert __version__


def test_cli_parser_builds():
    parser = build_parser()
    args = parser.parse_args(["generate", "-n", "5"])
    assert args.command == "generate"
    assert args.num == 5
