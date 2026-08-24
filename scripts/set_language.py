#!/usr/bin/env python3
"""Switch the active language of skills/agents. / 스킬·에이전트 활성 언어 전환.

Copies locales/<lang>/{skills,agents} docs over the active .claude/ copy.
Scripts under .claude/skills/*/scripts/ are shared and untouched.

Usage:
  python3 scripts/set_language.py ko   # Korean
  python3 scripts/set_language.py en   # English (default shipped)
"""
import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('ko', 'en'):
        sys.exit(__doc__)
    lang = sys.argv[1]
    src = os.path.join(REPO, 'locales', lang)
    copied = []

    skills_src = os.path.join(src, 'skills')
    for name in sorted(os.listdir(skills_src)):
        s = os.path.join(skills_src, name, 'SKILL.md')
        d = os.path.join(REPO, '.claude', 'skills', name, 'SKILL.md')
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
        copied.append(f"skills/{name}/SKILL.md")

    agents_src = os.path.join(src, 'agents')
    for name in sorted(os.listdir(agents_src)):
        if not name.endswith('.md'):
            continue
        shutil.copy2(os.path.join(agents_src, name),
                     os.path.join(REPO, '.claude', 'agents', name))
        copied.append(f"agents/{name}")

    print(f"active language -> {lang} ({len(copied)} files)")
    for c in copied:
        print(f"  .claude/{c}")


if __name__ == '__main__':
    main()
