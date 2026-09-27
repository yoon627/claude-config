#!/usr/bin/env python3
"""sync_codex_agents.py 단위 테스트 (stdlib unittest — TOML 파싱은 3.11+ tomllib, 없으면 tomli).

수동 실행:
    python3 scripts/bootstrap/test_sync_codex_agents.py
"""

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    import tomllib
except ImportError:  # python < 3.11 — 생성기는 3.9 에서도 돌지만 결과 검증에는 파서가 필요하다
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import sync_codex_agents as sync  # noqa: E402

# 빼는 절(병행 검토 호출 절차·출력 형식의 Codex 소절) 안에만 있는 문자열
REMOVED = ("Codex 병행", "preflight", "codex --version", "도메인 특화 프롬프트")
NEEDS_TOML = unittest.skipIf(tomllib is None, "TOML 파서 없음 — python 3.11+ 또는 tomli 필요")


def _load(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def _run(*args: str) -> int:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        return sync.main(list(args))


def _h2_outside_fences(text: str) -> list[str]:
    heads, fences = [], sync._Fences()
    for line in text.splitlines():
        if not fences.step(line) and fences.open is None and line.startswith("## "):
            heads.append(line)
    return heads


def _write_md(root: Path, name: str, body: str, tools: str = "Read") -> None:
    (root / f"{name}.md").write_text(
        f"---\nname: {name}\ndescription: d \"q\" \\ x\ntools: {tools}\nmodel: opus\n---\n{body}",
        encoding="utf-8",
    )


class RealAgentsTest(unittest.TestCase):
    @NEEDS_TOML
    def test_generates_valid_toml_without_codex_sections(self) -> None:
        sources = sorted((REPO / "agents").glob("*.md"))
        self.assertTrue(sources)
        texts = [md.read_text(encoding="utf-8") for md in sources]
        for s in REMOVED:  # 검사 문자열이 원본에 실제로 있어야 "없다" 가 의미를 갖는다
            self.assertTrue(any(s in t for t in texts), s)
        with TemporaryDirectory() as out:
            self.assertEqual(_run("--source", str(REPO / "agents"), "--out", out), 0)
            for md, raw in zip(sources, texts):
                meta, body = sync.parse_frontmatter(raw)
                path = Path(out) / f"{meta['name']}.toml"
                self.assertTrue(path.read_text(encoding="utf-8").startswith(sync.MARKER))
                data = _load(path)
                self.assertEqual(data["name"], meta["name"])
                self.assertEqual(data["description"], meta["description"])
                tools = {t.strip() for t in meta.get("tools", "").split(",") if t.strip()}
                expect_ro = bool(tools) and not tools & (sync.EDIT_TOOLS | {"Bash"})
                self.assertEqual("sandbox_mode" in data, expect_ro, md.name)
                text = data["developer_instructions"]
                for s in REMOVED:
                    self.assertNotIn(s, text, f"{md.name}: {s}")
                kept = [h for h in _h2_outside_fences(body) if not h.startswith("## Codex 병행")]
                self.assertEqual(_h2_outside_fences(text), kept, md.name)  # 빠진 절 말고는 다 남는다
                self.assertTrue(text.startswith(sync.preamble() + body.lstrip("\n")[:40]), md.name)

    def test_renamed_codex_heading_is_refused(self) -> None:
        raw = (REPO / "agents" / "code-reviewer.md").read_text(encoding="utf-8")
        self.assertIn("## Codex 병행 검토", raw)
        with TemporaryDirectory() as src, TemporaryDirectory() as out:
            (Path(src) / "code-reviewer.md").write_text(
                raw.replace("## Codex 병행 검토", "## Codex 교차 검토"), encoding="utf-8"
            )
            self.assertEqual(_run("--source", src, "--out", out), 2)
            self.assertEqual(list(Path(out).iterdir()), [])


class RenderTest(unittest.TestCase):
    @NEEDS_TOML
    def test_round_trip_escaping_and_section_boundaries(self) -> None:
        body = (
            "## 앞\n경로 C:\\tmp\\x 와 \"따옴표\" 와 \"\"\" 세 개\n\t탭\n"
            "## Codex 병행 검토 (optional)\n지워질 줄\n### 하위 절\n~~~\n## 블록 안\n~~~\n"
            "# H1 은 절을 끝낸다\n남는다\n"
            "## 가운데\n남는다\n"
            "```markdown\n## 템플릿\n- a\n## Codex 병행\n- 템플릿 안 소절도 지워진다\n## 뒤\n- b\n```\n"
            "## Codex 병행\n출력 형식도 지워진다\n````\n## 블록 안\n```\n여전히 블록\n````\n"
        )
        expected = (
            "## 앞\n경로 C:\\tmp\\x 와 \"따옴표\" 와 \"\"\" 세 개\n\t탭\n"
            "# H1 은 절을 끝낸다\n남는다\n## 가운데\n남는다\n"
            "```markdown\n## 템플릿\n- a\n## 뒤\n- b\n```\n"
        )
        with TemporaryDirectory() as src, TemporaryDirectory() as out:
            _write_md(Path(src), "x", "\n" + body)
            self.assertEqual(_run("--source", src, "--out", out), 0)
            data = _load(Path(out) / "x.toml")
            self.assertEqual(data["description"], 'd "q" \\ x')
            self.assertEqual(data["developer_instructions"], sync.preamble() + expected)
            self.assertEqual(set(data), {"name", "description", "sandbox_mode", "developer_instructions"})

    @NEEDS_TOML
    def test_sandbox_only_without_edit_or_shell(self) -> None:
        with TemporaryDirectory() as src, TemporaryDirectory() as out:
            _write_md(Path(src), "ro", "## a\n", tools="Read, Grep, WebSearch")
            _write_md(Path(src), "sh", "## a\n", tools="Read, Bash")
            _write_md(Path(src), "rw", "## a\n", tools="Read, Edit")
            self.assertEqual(_run("--source", src, "--out", out), 0)
            self.assertEqual(_load(Path(out) / "ro.toml")["sandbox_mode"], "read-only")
            self.assertNotIn("sandbox_mode", _load(Path(out) / "sh.toml"))
            self.assertNotIn("sandbox_mode", _load(Path(out) / "rw.toml"))

    def test_crlf_and_bom_frontmatter(self) -> None:
        meta, body = sync.parse_frontmatter("\ufeff---\r\nname: x\r\ndescription: d\r\n---\r\n## a\r\n")
        self.assertEqual((meta["name"], meta["description"], body), ("x", "d", "## a\n"))


class TargetsTest(unittest.TestCase):
    def test_rerun_noop_check_and_orphan_removal(self) -> None:
        with TemporaryDirectory() as src, TemporaryDirectory() as out:
            _write_md(Path(src), "x", "## a\nb\n")
            _write_md(Path(src), "gone", "## a\n")
            (Path(out) / "mine.toml").write_text("name = 'mine'\n", encoding="utf-8")
            self.assertEqual(_run("--source", src, "--out", out, "--check"), 1)
            self.assertEqual(sorted(p.name for p in Path(out).iterdir()), ["mine.toml"])
            self.assertEqual(_run("--source", src, "--out", out), 0)
            first = (Path(out) / "x.toml").stat().st_mtime_ns
            self.assertEqual(_run("--source", src, "--out", out, "--check"), 0)
            self.assertEqual(_run("--source", src, "--out", out), 0)
            self.assertEqual((Path(out) / "x.toml").stat().st_mtime_ns, first)
            _write_md(Path(src), "x", "## a\n바뀐 원본\n")
            self.assertEqual(_run("--source", src, "--out", out, "--check"), 1)
            (Path(src) / "gone.md").unlink()  # 생성 표식이 있고 원본이 사라진 사본은 지운다
            self.assertEqual(_run("--source", src, "--out", out, "--dry-run"), 0)
            self.assertTrue((Path(out) / "gone.toml").exists())
            self.assertEqual(_run("--source", src, "--out", out), 0)
            self.assertEqual(sorted(p.name for p in Path(out).iterdir()), ["mine.toml", "x.toml"])
            self.assertEqual((Path(out) / "mine.toml").read_text(encoding="utf-8"), "name = 'mine'\n")

    def test_renamed_case_keeps_one_current_copy(self) -> None:
        with TemporaryDirectory() as src, TemporaryDirectory() as out:
            _write_md(Path(src), "X", "## a\n")
            self.assertEqual(_run("--source", src, "--out", out), 0)
            (Path(src) / "X.md").unlink()
            _write_md(Path(src), "x", "## a\n")
            self.assertEqual(_run("--source", src, "--out", out), 0)
            left = sorted(Path(out).iterdir())  # 대소문자 구분 FS 는 x.toml, 구분 안 하는 FS 는 X.toml 하나
            self.assertEqual(len(left), 1)
            self.assertIn('name = "x"', left[0].read_text(encoding="utf-8"))

    def test_unmarked_or_linked_target_is_left_alone(self) -> None:
        with TemporaryDirectory() as src, TemporaryDirectory() as out, TemporaryDirectory() as elsewhere:
            for name in ("hand", "link", "ok"):
                _write_md(Path(src), name, "## a\n")
            (Path(out) / "hand.toml").write_text("name = 'hand'\n", encoding="utf-8")
            real = Path(elsewhere) / "real.toml"
            real.write_text("keep\n", encoding="utf-8")
            (Path(out) / "link.toml").symlink_to(real)
            self.assertEqual(_run("--source", src, "--out", out), 1)
            self.assertEqual((Path(out) / "hand.toml").read_text(encoding="utf-8"), "name = 'hand'\n")
            self.assertEqual(real.read_text(encoding="utf-8"), "keep\n")
            self.assertTrue((Path(out) / "ok.toml").read_text(encoding="utf-8").startswith(sync.MARKER))

    def test_unreadable_generated_copy_is_an_error_not_drift(self) -> None:
        with TemporaryDirectory() as src, TemporaryDirectory() as out:
            _write_md(Path(src), "x", "## a\n")
            (Path(out) / "x.toml").write_bytes(sync.MARKER.encode() + b"\n\xff\n")
            self.assertEqual(_run("--source", src, "--out", out, "--check"), 2)

    def test_dry_run_writes_nothing(self) -> None:
        with TemporaryDirectory() as src, TemporaryDirectory() as out:
            _write_md(Path(src), "x", "## a\nb\n")
            self.assertEqual(_run("--source", src, "--out", out, "--dry-run"), 0)
            self.assertEqual(list(Path(out).iterdir()), [])

    def test_one_bad_source_writes_nothing(self) -> None:
        cases = {
            "no-description": "---\nname: z\n---\n## a\n",
            "multi-line": "---\nname: z\ndescription: >\n  folded\n---\n## a\n",
            "no-frontmatter": "## a\n",
            "unclosed-fence": "---\nname: z\ndescription: d\n---\n## a\n```\n## b\n",
            "renamed-template-section": "---\nname: z\ndescription: d\n---\n## a\n```\n## Codex 교차\n- x\n```\n",
            "duplicate-name": "---\nname: a\ndescription: d\n---\n## a\n",
            "not-utf8": b"---\nname: z\ndescription: \xff\n---\n",
        }
        for label, text in cases.items():
            with self.subTest(label), TemporaryDirectory() as src, TemporaryDirectory() as out:
                _write_md(Path(src), "a", "## a\n")  # 정상 원본이 앞에 정렬돼도 쓰지 않는다
                data = text if isinstance(text, bytes) else text.encode("utf-8")
                (Path(src) / "z.md").write_bytes(data)
                self.assertEqual(_run("--source", src, "--out", out), 2)
                self.assertEqual(list(Path(out).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
