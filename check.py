import enum
import inspect
import operator
import typing

import typer
from plumbum import local
from plumbum.commands.processes import ProcessExecutionError
from plumbum.machines import LocalCommand
from rich import print

app = typer.Typer()

GREEN_CIRCLE = "🟢"
RED_CIRCLE = "🔴"


class Verbosity(enum.Enum):
    # typer enum can only be string
    quiet = "1"
    normal = "2"
    verbose = "3"

    @staticmethod
    def _compare(
        self: "Verbosity",
        other: "Verbosity_Comparable",
        _operator: typing.Callable[["Verbosity_Comparable", "Verbosity_Comparable"], bool],
    ) -> bool:
        match other:
            case Verbosity():
                return _operator(self.value, other.value)
            case int():
                return _operator(int(self.value), other)
            case str():
                return _operator(int(self.value), int(other))

    def __gt__(self, other: "Verbosity_Comparable") -> bool:
        # self > other
        return self._compare(self, other, operator.gt)

    def __ge__(self, other: "Verbosity_Comparable") -> bool:
        # self >= other
        return self._compare(self, other, operator.ge)

    def __lt__(self, other: "Verbosity_Comparable") -> bool:
        # self < other
        return self._compare(self, other, operator.lt)

    def __le__(self, other: "Verbosity_Comparable") -> bool:
        # self <= other
        return self._compare(self, other, operator.le)

    def __eq__(self, other: typing.Union["Verbosity", str, int, object]) -> bool:
        # self == other
        # eq is a special case because 'other' MUST be object according to mypy
        if other is Ellipsis or other is inspect._empty:
            # both instances of object; can't use Ellipsis or type(ELlipsis) = ellipsis as a type hint in mypy
            # special cases where Typer instanciates its cli arguments,
            # return False or it will crash
            return False
        if not isinstance(other, (str, int, Verbosity)):
            raise TypeError(f"Object of type {type(other)} can not be compared with Verbosity")
        return self._compare(self, other, operator.eq)

    def __hash__(self) -> int:
        # also required for Typer to work
        return hash(self.value)


Verbosity_Comparable = Verbosity | str | int

DEFAULT_VERBOSITY = Verbosity.normal


def info(*args: str) -> None:
    print(f"[blue]{' '.join(args)}[/blue]")


def warn(*args: str) -> None:
    print(f"[yellow]{' '.join(args)}[/yellow]")


def danger(*args: str) -> None:
    print(f"[red]{' '.join(args)}[/red]")


def log_command(command: LocalCommand, args: typing.Iterable[str]) -> None:
    info(f"> {command[*args]}")


def log_cmd_output(stdout: str, stderr: str) -> None:
    # if you are logging stdout, it's probably because it's not a successful run.
    # However, it's not stderr so we make it warning-yellow
    warn(stdout)
    # probably more important error stuff, so stderr goes last:
    danger(stderr)


def _check_tool(tool: str, *args: str, verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    cmd = local[tool]

    try:
        if verbosity >= 3:
            log_command(cmd, args)
        cmd(*args)
        print(GREEN_CIRCLE, tool)
    except ProcessExecutionError as e:
        if verbosity > 1:
            log_cmd_output(e.stdout, e.stderr)
        print(RED_CIRCLE, tool)


@app.command()
def ruff(verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    return _check_tool("ruff", ".", verbosity=verbosity)


@app.command()
def black(fix: bool = False, verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    args = [".", "--exclude=venv.+"]
    if not fix:
        if verbosity > 3:
            info("note: running WITHOUT --check -> changing files")
        args.append("--check")

    return _check_tool("black", *args, verbosity=verbosity)


@app.command()
def isort(fix: bool = False, verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    args = ["."]
    if not fix:
        if verbosity > 3:
            info("note: running WITHOUT --check -> changing files")
        args.append("--check-only")

    return _check_tool("isort", *args, verbosity=verbosity)


@app.command()
def mypy(verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    return _check_tool("mypy", ".", verbosity=verbosity)


@app.command()
def bandit(verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    return _check_tool("bandit", "-r", "-c", "pyproject.toml", ".", verbosity=verbosity)


@app.command()
def all(verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    """
    Run all available checks
    """
    ruff(verbosity=verbosity)
    black(verbosity=verbosity)
    mypy(verbosity=verbosity)
    bandit(verbosity=verbosity)
    isort(verbosity=verbosity)


@app.command()
def fix(verbosity: Verbosity = DEFAULT_VERBOSITY) -> None:
    """
    Do everything that's safe to fix (so not ruff because that may break semantics)
    """
    black(fix=True, verbosity=verbosity)
    isort(fix=True, verbosity=verbosity)


if __name__ == "__main__":
    app()
