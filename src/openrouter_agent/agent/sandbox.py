import os
import shutil
import logging

log = logging.getLogger(__name__)


class Sandbox:
    @staticmethod
    def prepare(base_workdir: str, episode_id: str) -> str:
        epdir = os.path.join(base_workdir, f"ep_{episode_id}")
        os.makedirs(epdir, exist_ok=True)
        log.info(f"sandbox prepared: {epdir}")
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
        log.info(f"snapshot created: {backup_dir}")
        return backup_dir
