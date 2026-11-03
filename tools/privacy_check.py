#!/usr/bin/env python3
"""Read-only privacy checks for worktrees, staged files and reachable Git history.

Private literals belong in an external JSON config, never in this source file.
Reports contain locations and rule IDs only, never matching personal values.
Exit codes: 0 clean, 1 findings, 2 incomplete inspection/configuration error.
"""
import argparse
import bz2
import gzip
import io
import json
import lzma
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tarfile
import zipfile
import zlib


DEFAULT_ALLOWED_HOME_USERS = {'user', 'runner', 'example', 'username'}
HOME_PATH = re.compile(r'(?:/home/|/Users/)([A-Za-z0-9_.-]+)(?:/|\b)|[A-Za-z]:[\\/]Users[\\/]([A-Za-z0-9_.-]+)', re.I)
SECRET_RULES = [
    ('claude-session-link', re.compile(r'https?://claude\.ai/code/session_[A-Za-z0-9]+', re.I)),
    ('private-key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----')),
    ('github-token', re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b')),
    ('aws-access-key', re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b')),
    ('assistant-artifact-identifier', re.compile(r'\boutputs[\\/][0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}(?:[\\/]|\b)', re.I)),
]


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)


def elf_payloads(raw):
    """Inspect compressed debug sections too; raw strings alone miss these."""
    if not raw.startswith(b'\x7fELF') or len(raw) < 64:
        return
    bits, byteorder = raw[4], raw[5]
    endian = '<' if byteorder == 1 else '>'
    if bits == 2:
        section_offset = struct.unpack_from(endian + 'Q', raw, 40)[0]
        entry_size, count, names_index = struct.unpack_from(endian + 'HHH', raw, 58)
        layout = endian + 'IIQQQQIIQQ'
    elif bits == 1:
        section_offset = struct.unpack_from(endian + 'I', raw, 32)[0]
        entry_size, count, names_index = struct.unpack_from(endian + 'HHH', raw, 46)
        layout = endian + 'IIIIIIIIII'
    else:
        raise ValueError('unsupported ELF class')
    if not count or not section_offset:
        return
    minimum = struct.calcsize(layout)
    if entry_size < minimum or section_offset + entry_size * count > len(raw):
        raise ValueError('invalid ELF section table')
    sections = [struct.unpack_from(layout, raw, section_offset + entry_size * i) for i in range(count)]
    if names_index >= len(sections):
        raise ValueError('invalid ELF section-name table')
    names_header = sections[names_index]
    names = raw[names_header[4]:names_header[4] + names_header[5]]
    for header in sections:
        name = names[header[0]:].split(b'\0', 1)[0].decode('ascii', 'replace')
        data = raw[header[4]:header[4] + header[5]]
        if name == '.gnu_debugdata':
            yield name, lzma.decompress(data)
        elif name.startswith('.zdebug') and data.startswith(b'ZLIB'):
            yield name, zlib.decompress(data[12:])
        elif header[2] & 0x800:  # SHF_COMPRESSED
            compression = struct.unpack_from(endian + 'I', data)[0]
            offset = 24 if bits == 2 else 12
            if compression != 1:
                raise ValueError('unsupported ELF debug compression')
            yield name, zlib.decompress(data[offset:])


def png_payloads(raw):
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        return
    offset = 8
    while offset + 12 <= len(raw):
        length = struct.unpack_from('>I', raw, offset)[0]
        kind = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + length]
        if len(data) != length or offset + length + 12 > len(raw):
            raise ValueError('truncated PNG chunk')
        if kind == b'zTXt':
            keyword, tail = data.split(b'\0', 1)
            if not tail or tail[0] != 0:
                raise ValueError('unsupported PNG text compression')
            yield 'zTXt', zlib.decompress(tail[1:])
        elif kind == b'iTXt':
            keyword, tail = data.split(b'\0', 1)
            if len(tail) < 2:
                raise ValueError('truncated PNG international text')
            compressed, method = tail[:2]
            language, translated, payload = tail[2:].split(b'\0', 2)
            if compressed:
                if method != 0:
                    raise ValueError('unsupported PNG text compression')
                payload = zlib.decompress(payload)
            yield 'iTXt', payload
        offset += length + 12
        if kind == b'IEND':
            break


class Scanner:
    def __init__(self, config=None, max_bytes=256 * 1024 * 1024):
        config = config or {}
        self.max_bytes = max_bytes
        self.rules = list(SECRET_RULES)
        for i, literal in enumerate(config.get('forbidden_literals', [])):
            if not isinstance(literal, str) or not literal:
                raise ValueError('forbidden literals must be nonempty strings')
            self.rules.append((f'private-literal-{i + 1}', re.compile(re.escape(literal), re.I)))
        for i, expression in enumerate(config.get('forbidden_regex', [])):
            self.rules.append((f'private-pattern-{i + 1}', re.compile(expression, re.I)))
        self.allowed_home_users = DEFAULT_ALLOWED_HOME_USERS | set(config.get('allowed_home_users', []))
        self.findings = []
        self.errors = []
        self.checked = 0
        self._seen_findings = set()

    def finding(self, source, rule, line=None):
        item = (source, rule, line)
        if item not in self._seen_findings:
            self._seen_findings.add(item)
            self.findings.append({'source': source, 'rule': rule, **({'line': line} if line else {})})

    def text(self, source, value):
        for rule, pattern in self.rules:
            for match in pattern.finditer(value):
                self.finding(source, rule, value.count('\n', 0, match.start()) + 1)
        # Third-party dependencies can contain unrelated upstream sample homes.
        # Private rules above still inspect every byte of those dependencies.
        if 'offline_deps/' not in source.replace('\\', '/'):
            for match in HOME_PATH.finditer(value):
                account = match[1] or match[2]
                if account.casefold() not in self.allowed_home_users:
                    self.finding(source, 'personal-home-path', value.count('\n', 0, match.start()) + 1)

    def data(self, source, raw, depth=0):
        self.checked += 1
        if len(raw) > self.max_bytes:
            self.errors.append({'source': source, 'error': 'inspection-size-limit'})
            return
        self.text(source, raw.decode('utf-8', 'replace'))
        if b'\0' in raw:
            # Binary metadata and UTF-16 documents can contain personal values.
            for codec in ('utf-16-le', 'utf-16-be'):
                self.text(source, raw.decode(codec, 'ignore'))
        try:
            recursive_container = (raw.startswith((b'\x7fELF', b'\x89PNG\r\n\x1a\n', b'%PDF',
                b'PK\x03\x04', b'PK\x05\x06', b'\x1f\x8b', b'\xfd7zXZ', b'BZh',
                b'7z\xbc\xaf\x27\x1c', b'Rar!\x1a\x07')) or (len(raw) > 262 and raw[257:262] == b'ustar'))
            if depth >= 6 and recursive_container:
                raise ValueError('container nesting limit')
            for name, payload in elf_payloads(raw):
                self.data(source + '!' + name, payload, depth + 1)
            for name, payload in png_payloads(raw):
                self.data(source + '!' + name, payload, depth + 1)
            if raw.startswith(b'%PDF'):
                # Covers compressed metadata and ordinary Flate text streams.
                # Complex font encodings and image text still require visual QA.
                for index, match in enumerate(re.finditer(rb'<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream', raw, re.S)):
                    if b'/FlateDecode' in match[1]:
                        self.data(source + '!<PDF-Flate-' + str(index) + '>', zlib.decompress(match[2]), depth + 1)
            if raw.startswith((b'PK\x03\x04', b'PK\x05\x06')):
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    total = sum(member.file_size for member in archive.infolist())
                    if total > self.max_bytes:
                        raise ValueError('archive expansion limit')
                    for member in archive.infolist():
                        self.text(source + '!<member-name>', member.filename)
                        if not member.is_dir():
                            self.data(source + '!' + member.filename, archive.read(member), depth + 1)
                    self.text(source + '!<archive-comment>', archive.comment.decode('utf-8', 'replace'))
            elif raw.startswith(b'\x1f\x8b'):
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as archive:
                    payload = archive.read(self.max_bytes + 1)
                self.data(source + '!<gzip>', payload, depth + 1)
            elif raw.startswith(b'\xfd7zXZ'):
                with lzma.LZMAFile(io.BytesIO(raw)) as archive:
                    payload = archive.read(self.max_bytes + 1)
                self.data(source + '!<xz>', payload, depth + 1)
            elif raw.startswith(b'BZh'):
                with bz2.BZ2File(io.BytesIO(raw)) as archive:
                    payload = archive.read(self.max_bytes + 1)
                self.data(source + '!<bzip2>', payload, depth + 1)
            elif raw.startswith((b'7z\xbc\xaf\x27\x1c', b'Rar!\x1a\x07')):
                raise ValueError('archive format requires separate inspection')
            elif len(raw) > 262 and raw[257:262] == b'ustar':
                with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
                    for member in archive:
                        self.text(source + '!<member-name>', member.name)
                        if member.issym() or member.islnk():
                            self.text(source + '!' + member.name, member.linkname)
                        elif member.isfile():
                            if member.size > self.max_bytes:
                                raise ValueError('archive expansion limit')
                            self.data(source + '!' + member.name, archive.extractfile(member).read(), depth + 1)
        except (ValueError, OSError, EOFError, struct.error, zipfile.BadZipFile, tarfile.TarError, RuntimeError, lzma.LZMAError, zlib.error) as error:
            self.errors.append({'source': source, 'error': type(error).__name__})

    def worktree(self, repo):
        for base, dirs, names in os.walk(repo, followlinks=False):
            dirs[:] = sorted(name for name in dirs if name != '.git')
            for name in sorted([name for name in names if name != '.git'] + [d for d in dirs if (Path(base) / d).is_symlink()]):
                path = Path(base) / name
                source = path.relative_to(repo).as_posix()
                self.text('<path-name>', source)
                try:
                    raw = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
                    self.data(source, raw)
                except OSError as error:
                    self.errors.append({'source': source, 'error': type(error).__name__})

    def staged(self, repo):
        entries = git(repo, 'ls-files', '--stage', '-z').split(b'\0')
        changed = set(git(repo, 'diff', '--cached', '--name-only', '--diff-filter=ACMR', '-z').split(b'\0'))
        for entry in entries:
            if not entry:
                continue
            metadata, filename = entry.split(b'\t', 1)
            if filename not in changed:
                continue
            mode, oid, stage = metadata.split()
            source = filename.decode('utf-8', 'replace')
            self.text('<staged-path-name>', source)
            if stage != b'0':
                self.errors.append({'source': source, 'error': 'unmerged-index-entry'})
            elif mode == b'160000':
                self.errors.append({'source': source, 'error': 'submodule-needs-separate-inspection'})
            else:
                self.data('index:' + source, git(repo, 'cat-file', 'blob', oid.decode()))
        for key in ('GIT_AUTHOR_IDENT', 'GIT_COMMITTER_IDENT'):
            self.text('<next-commit:' + key + '>', git(repo, 'var', key).decode('utf-8', 'replace'))

    def history(self, repo):
        for ref in git(repo, 'for-each-ref', '--format=%(refname)').decode().splitlines():
            self.text('<ref-name>', ref)
        objects = git(repo, 'rev-list', '--objects', '--all').splitlines()
        process = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            for row in objects:
                oid, _, filename = row.partition(b' ')
                process.stdin.write(oid + b'\n')
                process.stdin.flush()
                header = process.stdout.readline().split()
                if len(header) != 3:
                    raise ValueError('invalid Git object response')
                kind, size = header[1], int(header[2])
                raw = process.stdout.read(size)
                if len(raw) != size or process.stdout.read(1) != b'\n':
                    raise ValueError('truncated Git object')
                source = 'git:' + oid.decode() + (':' + filename.decode('utf-8', 'replace') if filename else '')
                if filename:
                    self.text('<historical-path-name>', filename.decode('utf-8', 'replace'))
                # A blob may have many filenames: rev-list emits only one.
                # Raw tree entries cover all names, including identical blobs.
                if kind in (b'blob', b'commit', b'tag', b'tree'):
                    self.data(source, raw)
        finally:
            process.stdin.close()
            process.stdout.close()
            if process.wait() != 0:
                self.errors.append({'source': '<git-history>', 'error': 'git-cat-file-failed'})

    def result(self):
        return {'checked_items': self.checked, 'findings': self.findings, 'errors': self.errors,
                'complete': not self.errors, 'clean': not self.errors and not self.findings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--config', type=Path, help='PRIVATE JSON config stored outside the repository')
    parser.add_argument('--history', action='store_true', help='also inspect all reachable Git objects and refs')
    parser.add_argument('--staged', action='store_true', help='inspect index additions/modifications and the next commit identity')
    parser.add_argument('--history-only', action='store_true')
    parser.add_argument('--message-file', type=Path, help='inspect the actual pending commit message')
    parser.add_argument('--output', type=Path, help='write JSON report (outside repository recommended)')
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.config.read_text()) if args.config else {}
        scanner = Scanner(config)
        repo = args.repo.resolve()
        if args.message_file:
            scanner.data('<pending-commit-message>', args.message_file.read_bytes())
        elif args.staged:
            scanner.staged(repo)
        elif not args.history_only:
            scanner.worktree(repo)
        if args.history or args.history_only:
            scanner.history(repo)
        result = scanner.result()
    except (ValueError, OSError, subprocess.CalledProcessError, re.error) as error:
        # Exception text might itself contain a sensitive absolute path/value.
        result = {'clean': False, 'complete': False, 'findings': [], 'errors': [{'error': type(error).__name__}]}
    report = json.dumps(result, ensure_ascii=True, indent=2) + '\n'
    if args.output:
        args.output.write_text(report)
        print(json.dumps({key: value for key, value in result.items() if key not in ('findings', 'errors')}))
    else:
        print(report, end='')
    return 2 if not result['complete'] else int(not result['clean'])


if __name__ == '__main__':
    sys.exit(main())
