import os
import shutil
import subprocess
import logging
from typing import Dict, Any, List, Optional
from difflib import unified_diff

log = logging.getLogger(__name__)


class Executor:
    def __init__(self, workdir: str):
        self.workdir = workdir

    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        action = step.get("action", "")
        handlers = {
            "write_file": self._write_file,
            "run_file": self._run_file,
            "read_file": self._read_file,
            "print": self._do_print,
            "explain": self._explain,
            "test": self._test,
        }
        handler = handlers.get(action)
        if not handler:
            return {"success": False, "error": f"unknown action: {action}"}
        return handler(step)

    def _write_file(self, step: Dict[str, Any]) -> Dict[str, Any]:
        fn = step.get("filename")
        content = step.get("content", "")
        if not fn or content is None:
            return {"success": False, "error": "invalid write_file step (filename/content missing)"}
        path = os.path.join(self.workdir, fn)
        try:
            dirname = os.path.dirname(path)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "output": f"WROTE {fn}"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    def _run_file(self, step: Dict[str, Any]) -> Dict[str, Any]:
        fn = step.get("filename")
        args = step.get("args", [])
        if not fn:
            return {"success": False, "error": "invalid run_file step (filename missing)"}
        path = os.path.join(self.workdir, fn)
        if not os.path.exists(path):
            return {"success": False, "output": "", "error": f"file not found: {fn}"}
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if "input(" in content:
            return {"success": False, "output": "", "error": "interactive_program_requires_input"}
        cmd = ["python", path] + [str(a) for a in args]
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            out = (p.stdout or "").strip()
            err = (p.stderr or "").strip()
            if p.returncode == 0:
                return {"success": True, "output": out}
            return {"success": False, "output": out, "error": err or f"exit code {p.returncode}"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    def _read_file(self, step: Dict[str, Any]) -> Dict[str, Any]:
        fn = step.get("filename")
        if not fn:
            return {"success": False, "error": "invalid read_file step (filename missing)"}
        path = os.path.join(self.workdir, fn)
        if not os.path.exists(path):
            return {"success": False, "output": "", "error": f"file not found: {fn}"}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return {"success": True, "output": f.read()}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    def _do_print(self, step: Dict[str, Any]) -> Dict[str, Any]:
        text = step.get("text", "")
        print(text)
        return {"success": True, "output": text}

    def _explain(self, step: Dict[str, Any]) -> Dict[str, Any]:
        fn = step.get("filename")
        if not fn:
            return {"success": False, "error": "invalid explain step (filename missing)"}
        r = self._read_file(step)
        if not r.get("success"):
            return r
        return {"success": True, "output": r.get("output", ""), "_needs_llm_explain": True, "filename": fn}

    def _test(self, step: Dict[str, Any]) -> Dict[str, Any]:
        fn = step.get("filename")
        tests = step.get("tests")
        if tests:
            results = []
            for t in tests:
                args = t.get("args", [])
                expected = t.get("expected", "")
                r = self._run_file({"filename": fn, "args": args})
                ok = r.get("success") and (expected == "" or expected in r.get("output", ""))
                results.append({"args": args, "success": ok, "output": r.get("output", ""), "error": r.get("error", "")})
            return {"success": all(r["success"] for r in results), "output": results}
        return self._run_file({"filename": fn, "args": []})

    def read_file_content(self, filename: str) -> Optional[str]:
        r = self._read_file({"filename": filename})
        return r.get("output") if r.get("success") else None

    @staticmethod
    def compute_diff(before: Optional[str], after: Optional[str]) -> str:
        a = before.splitlines(keepends=True) if before else []
        b = after.splitlines(keepends=True) if after else []
        return ''.join(unified_diff(a, b, fromfile='before', tofile='after'))


class Sandbox:
    @staticmethod
    def prepare(base_workdir: str, episode_id: str) -> str:
        epdir = os.path.join(base_workdir, f"ep_{episode_id}")
        os.makedirs(epdir, exist_ok=True)
        return epdir

    @staticmethod
    def snapshot(base_workdir: str, epdir: str) -> str:
        backup_dir = os.path.join(epdir, "backup_before")
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        os.makedirs(backup_dir, exist_ok=True)
        for root, _, files in os.walk(base_workdir):
            if root.startswith(os.path.join(base_workdir, "ep_")):
                continue
            for f in files:
                src = os.path.join(root, f)
                rel = os.path.relpath(src, base_workdir)
                dst = os.path.join(backup_dir, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        return backup_dir
