#!/usr/bin/env python3

from __future__ import annotations

from datetime import timedelta
import importlib
import inspect
import os
from pathlib import Path
import sys
import time
from typing import Any
import unittest

from rich import box, pretty
from rich.abc import RichRenderable
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, MofNCompleteColumn, SpinnerColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn, TextColumn
from rich.rule import Rule
from rich import status
from rich.syntax import Syntax
from rich.text import Text
from rich.traceback import Traceback

from pypbt import PyPBT, domains
from pypbt.quantifiers import CounterExample, is_qcproperty, ok, PredicateError


IGNORE = (
    '__pycache__',
)

# TODO
Candidate = object


def code_panel(
        fun: Callable,
        title: str= "",
        title_align: str= 'left',
        truncate: bool= True,
) -> Panel:
    try:
        source_lines, line_no = inspect.getsourcelines(fun)
    except OSError:
        source_lines = None
    if source_lines is not None:
        if not truncate:
            source = "".join(source_lines)
        else:
            i = 0
            for line in source_lines:
                if line.strip().startswith("def "):
                    break
                i += 1
            if len(source_lines) < i + 4:
                source = "".join(source_lines)
            else:
                source = "".join(source_lines[:i+4]) + "···"

        # TODO: Truncate after n lines of predicate
        s = Syntax(
            code= source.strip(),
            lexer= 'python',
            line_numbers= True,
            start_line= line_no
        )
    else:
        s = Syntax(code= str(fun), lexer= 'python')
    return Panel(s, box= box.ROUNDED, title= title, title_align= title_align)


def env_panel(env: dict, title:str= "") -> Panel:
    s = "\n".join(f"{k} = {pretty.traverse(v)}" for k, v in env.items())
    return Panel(s, box= box.ROUNDED, expand= False, title= title)


def traceback_from_exception(exc: Exception) -> Traceback:
    return Traceback.from_exception(
        exc_type= type(exc),
        exc_value= exc,
        traceback= exc.__traceback__,
        show_locals= True,
    )


def spinner_progress(spinner:str= 'pong') -> Progress:
    return  Progress(
        TextColumn("[progress.description]{task.description}"),
        SpinnerColumn(spinner),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        transient= True,
    )


class ReporterMixin:
    def _report_summary(self, *lines: Sequence[str], console: Console, title: str) -> None:
        console.print(Panel("\n".join(lines), title= title))


# --------------------------------------------------------------------------------------
# Unittest
# --------------------------------------------------------------------------------------
loader = unittest.TestLoader()


class UnittestResult(unittest.TestResult):
    def __init__(self, console: Console, status: Status):
        super().__init__()
        self.console = console
        self.status = status
        self.tests_run = 0
        self.n_success = 0

    def get_description(self, test):
        doc_first_line = test.shortDescription()
        if doc_first_line:
            return f"{test}\n{doc_first_line}"
        else:
            return test._testMethodName
        
    def startTest(self, test):
        self.tests_run += 1
        self.status.update(status= f"  {self.get_description(test)} ...")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            self.n_success += 1
        else:
            if issubclass(err[0], subtest.failureException):
                exctype, value, tb = err
                # Sólo queremos el último frame. Es donde está el assert que falló.
                while tb.tb_next is not None:
                    tb = tb.tb_next
                tb = Traceback.from_exception(exctype, value, tb, show_locals= True)
                self.console.print(tb)
                self.console.print(f"{self.get_description(test)} [red]FAILED[/red]")
            else:
                exctype, value, tb = err
                tb = Traceback.from_exception(exctype, value, tb, show_locals= True)
                self.console.print(tb)
                self.console.print(f"{self.get_description(test)} [red]ERROR[/red]")
   
    def addSuccess(self, test):
        self.n_success += 1
        self.console.print(f"{self.get_description(test)} [green]PASSED[/green]")

    def addError(self, test, err):
        super().addError(test, err)
        exctype, value, tb = err
        tb = Traceback.from_exception(exctype, value, tb, show_locals= True)
        self.console.print(tb)
        self.console.print(f"{self.get_description(test)} [red]ERROR[/red]")


    def addFailure(self, test, err):
        super().addFailure(test, err)
        exctype, value, tb = err
        # Sólo queremos el último frame. Es donde está el assert que falló.
        while tb.tb_next is not None:
            tb = tb.tb_next
        tb = Traceback.from_exception(exctype, value, tb, show_locals= True)
        self.console.print(tb)
        self.console.print(f"{self.get_description(test)} [red]FAILED[/red]")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.console.print(
            f"{self.get_description(test)}"
            f" [yellow]SKIPPED [dim]\"{reason}\"[/dim][/yellow]"
        )

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        exctype, value, tb = err
        self.console.print(
            f"{self.get_description(test)}"
            f" [yellow]Expected failure {exctype.__name__}(\"{value}\")[/yellow]"
        )
        
    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.console.print(
            f"{self.get_description(test)}"
            f" [red]Unexpected success[/red]"
        )

        
class UnittestRunner(ReporterMixin):
    def __init__(self):
        self.tests_run = 0
        self.n_success = 0
        self.n_errors = 0
        self.n_failures = 0
        self.n_skipped = 0
        self.n_expected_failures = 0
        self.n_unexpected_successes = 0
        self.elapsed_total = 0
                
    def wants_to_iter_dir(self, dir: Path) -> bool:
        return True

    def wants_to_run_file(self, file: Path) -> bool:
        return file.suffix == ".py"

    def will_do(self, test: Any) -> bool:
        return isinstance(test, type) and issubclass(test, unittest.TestCase)

    def do_test(self, test: Any, console: Console) -> None:
        console.rule(title= f"[b]{test.__name__}[/b]", align= 'left')
        tests = loader.loadTestsFromTestCase(test)
        with console.status(f"[b]{test.__name__}[/b]") as status:
            result = UnittestResult(console, status)
            start_time = time.perf_counter()
            tests(result)
            stop_time = time.perf_counter()
            e_time = stop_time - start_time
        self.elapsed_total += e_time
        self.tests_run += result.tests_run
        self.n_success += result.n_success
        self.n_errors += len(result.errors)
        self.n_failures += len(result.failures)
        self.n_skipped += len(result.skipped)
        self.n_expected_failures += len(result.expectedFailures)
        self.n_unexpected_successes += len(result.unexpectedSuccesses)
        console.rule(title= "")
        console.line()

    def report_summary(self, console: Console) -> None:
        if self.tests_run == 0:
            return
        delta = timedelta(seconds= self.elapsed_total)
        self._report_summary(
            f"tests run: {self.tests_run} [progress.elapsed]({delta})[/]",
            f"success: {self.n_success}",
            f"failures: {self.n_failures}",
            *([f"errors: {self.n_errors}"] if self.n_errors > 0 else []),
            *([f"skipped: {self.n_skipped}"] if self.n_skipped > 0 else []),
            *([f"expected failures: {self.n_expected_failures}"] if self.n_expected_failures > 0 else []),
            *([f"unexpected successes: {self.n_unexpected_successes}"] if self.n_unexpected_successes > 0 else []),
            title= f"[b]unittest[/b]",
            console= console,
        )
        

# --------------------------------------------------------------------------------------
# Hypothesis
# --------------------------------------------------------------------------------------
class HypothesisRunner(ReporterMixin):
    def __init__(self):
        self.n_properties = 0
        self.n_falsifying_examples = 0
        self.n_errors = 0
        self.elapsed_total = 0

    def wants_to_iter_dir(self, dir: Path) -> bool:
        return True

    def wants_to_run_file(self, file: Path) -> bool:
        return file.suffix == ".py"

    def will_do(self, test: Any) -> bool:
        return getattr(test, 'is_hypothesis_test', False)

    def do_test(self, test: Any, console: Console) -> None:
        self.n_properties += 1
        console.print(code_panel(test))
        from contextlib import redirect_stdout
        import io
        capture = io.StringIO()
        try:
            start_time = time.perf_counter()
            with redirect_stdout(capture):
                test()
            stop_time = time.perf_counter()
            console.print("[green]PASSED[/green]")
        except AssertionError:
            stop_time = time.perf_counter()
            self.n_falsifying_examples += 1
            console.print_exception()
            console.print(Panel(capture.getvalue(), title= "", expand= False))
        except:
            stop_time = time.perf_counter()
            self.n_errors += 1
            console.print_exception()
        e_time = stop_time - start_time
        self.elapsed_total += e_time
        console.line()
        
    def report_summary(self, console: Console) -> None:
        if self.n_properties == 0:
            return
        delta = timedelta(seconds= self.elapsed_total)
        self._report_summary(
            f"properties checked: {self.n_properties} [progress.elapsed]({delta})[/]",
            f"total number of falsifying examples found: {self.n_falsifying_examples}",
            *([f"total number of buggy properties: {self.n_errors}"] if self.n_errors > 0 else []),
            title= "[b]Hypothesis[/b]",
            console= console,
        )

        
# --------------------------------------------------------------------------------------
# PyPBT
# --------------------------------------------------------------------------------------
class PyPbtRunner(ReporterMixin):
    def __init__(self):
        self.n_properties = 0
        self.n_samples = 0
        self.n_counterexamples = 0
        self.n_errors = 0
        self.elapsed_total = 0
        
    def wants_to_iter_dir(self, dir: Path) -> bool:
        return True

    def wants_to_run_file(self, file: Path) -> bool:
        return file.suffix == ".py"
    
    def will_do(self, test: Any) -> bool:
        return is_qcproperty(test)

    def do_test(self, test: Any, console: Console) -> None:
        prop = test
        console.print(code_panel(prop.get_predicate()))
        self.n_properties += 1
        with spinner_progress() as progress:
            task = progress.add_task("Testing...", total= None)
            for i, result in enumerate(prop(env= {}), start= 1):
                if result is ok:
                    progress.advance(task)
                    self.n_samples += 1
                elif isinstance(result, CounterExample):
                    progress.stop()
                    self.n_counterexamples += 1
                    console.print(env_panel(result.env, title= " counterexample "))
                    n_tests = f"{i} tests" if i>1 else "1 test"
                    msg = f"[red]FAILED[/red] after {n_tests}"
                    break
                elif isinstance(result, PredicateError):
                    progress.stop()
                    self.n_errors += 1
                    console.print(traceback_from_exception(result.exc))
                    console.print(env_panel(result.env, title= " counterexample "))
                    n_tests = f"{i} tests" if i>1 else "1 test"
                    msg = f"[red]FAILED[/red] after {n_tests}"
                    break
                else:
                    raise RuntimeError(f"Unkown {result=}")
            else:
                progress.stop()
                n_tests = f"{i} tests" if i>1 else "1 test"
                msg = f"[green]PASSED[/green] {n_tests}"
            elapsed = progress.tasks[task].elapsed
            delta = timedelta(seconds= elapsed)
            console.print(f"{msg} [progress.elapsed]({delta})[/]")
            self.elapsed_total += elapsed
            console.line(2)

    def report_summary(self, console: Console) -> None:
        if self.n_properties == 0:
            return
        delta = timedelta(seconds= self.elapsed_total)
        self._report_summary(
            f"properties checked: {self.n_properties} [progress.elapsed]({delta})[/]",
            f"total number of samples checked: {self.n_samples}",
            f"total number of counterexamples found: {self.n_counterexamples}",
            *([f"number of errors: {self.n_errors}"] if self.n_errors > 0 else []),
            title= f"[b]{PyPBT}[/b]",
            console= console,
        )


# --------------------------------------------------------------------------------------
# EBT
# --------------------------------------------------------------------------------------
TEST_ATTR = '__test_title__'


def test(title: str) -> Callable[[Callable],Callable]:
    def decorator(fun: Callable) -> Callable:
        setattr(fun, TEST_ATTR, title)
        return fun
    return decorator

    
class KissEBTRunner(ReporterMixin):
    def __init__(self):
        self.tests_run = 0
        self.n_success = 0
        self.n_failures = 0
        self.n_errors = 0
        self.elapsed_total = 0

    def want_to_iter_dir(self, dir: Path) -> bool:
        return True

    def wants_to_run_file(self, file: Path) -> bool:
        return file.suffix == ".py"

    def will_do(self, test: Any) -> bool:
        return hasattr(test, TEST_ATTR)

    def do_test(self, test: Any, console: Console) -> None:
        title = getattr(test, TEST_ATTR)
        with console.status(f"{title} ..."):
            start_time = time.perf_counter()
            try:
                test()
            except Exception as e:
                stop_time = time.perf_counter()
                exception = e
            else:
                stop_time = time.perf_counter()
                exception = None
        self.tests_run += 1
        e_time = stop_time - start_time
        self.elapsed_total += e_time
        delta = timedelta(seconds= e_time)
        if exception is None:
            self.n_success += 1
            console.print(f"[b]{title}[/b] [green]PASSED[/green] [progress.elapsed]({delta})[/]")
        elif isinstance(exception, AssertionError):
            self.n_failures += 1
            console.print(traceback_from_exception(exception))
            console.print(f"[b]{title}[/b] [red]FAILED[/red] [progress.elapsed]({delta})[/]")
        else:
            self.n_errors += 1
            console.print_exception()
            console.print(
                f"[b]{title}[/b] [red]ERROR \"Unexpected exception\"[/red]"
                f" [progress.elapsed]({delta})[/]")

        
    def report_summary(self, console: Console) -> None:
        if self.tests_run == 0:
            return
        delta = timedelta(seconds= self.elapsed_total)
        self._report_summary(
            f"tests run: {self.tests_run} [progress.elapsed]({delta})[/]",
            f"success: {self.n_success}",
            f"failures: {self.n_failures}",
            *([f"errors: {self.n_errors}"] if self.n_errors > 0 else []),
            title= f"[b]EBT[/b]",
            console= console,
        )


# --------------------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------------------

def collect_objs_from_file(file: Path, console: Console) -> Iterator:
    parent = str(file.parent)
    module_name = file.stem
    if parent not in sys.path:
        sys.path.append(parent)
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        console.print_exception()
        module = None
    if module is not None:
        for name in dir(module):
            obj = getattr(module, name)
            yield obj
        

def collect_objs(
        path: Path,
        candidates: tuple[Candidate],
        console: Console
) -> Iterator[tuple[Any, tuple[Candidate]]]:
    if path.name in IGNORE:
        return
    if path.is_dir():
        dir_name = f"{path}{os.sep}"
        candidates= tuple(candidate for candidate in candidates
                          if candidate.wants_to_iter_dir(path))
        if len(candidates) ==  0:
            console.print(Rule(title= f" Skipping (no runners): {dir_name} ", characters= "="))
        else:
            console.print(Rule(title= f" [b]Entering dir: {dir_name}[/b] ", characters= "="))
            console.line()
            for child in path.iterdir():
                yield from collect_objs(
                    path= child,
                    candidates= candidates,
                    console= console
                )
            console.print(Rule(title= f" Leaving: {dir_name} ", characters= "-"))
            console.line()
                
    elif path.is_file():
        candidates= tuple(candidate for candidate in candidates
                          if candidate.wants_to_run_file(path))
        if len(candidates) ==  0:
            console.print(Rule(title= f" Skipping (no runners): {path} ", characters= "="))
        else:
            console.print(Rule(title= f" [b]Collecting: {path}[/b] ", characters= "="))
            console.line()
            for obj in collect_objs_from_file(file= path, console= console):
                yield obj, candidates
            console.print(Rule(title= f" Finished: {path} ", characters= "-"))
            console.line()
                
    elif not path.exists():
        # TODO: Better message
        print(f"ERROR: File not found: {path}")
        sys.exit(1)
        
    else:
        # TODO: Better message
        raise RuntimeError(f"{path} is not regular file nor directory")
                
    
def main():
    if len(sys.argv) < 2:
        cmd = Path(sys.argv[0]).name
        print(f"USAGE: {cmd} <props_files|dirs>")
        sys.exit(1)

    CANDIDATES = (
        PyPbtRunner(),
        HypothesisRunner(),
        UnittestRunner(),
        KissEBTRunner(),
    )
    seed = domains.seed
    console = Console()
    for arg in sys.argv[1:]:
        path = Path(arg)
        for obj, candidates in collect_objs(
                path= path,
                candidates= CANDIDATES,
                console= console):
            candidate = next((candidate for candidate in candidates
                              if candidate.will_do(obj)), None)
            if candidate is not None:
                candidate.do_test(obj, console)
    console.print(
        Panel(
            f"started with seed: {seed}",
            title= ""
        )
    )
    for candidate in CANDIDATES:
        candidate.report_summary(console)
        
            
if __name__ == '__main__':
    main()
