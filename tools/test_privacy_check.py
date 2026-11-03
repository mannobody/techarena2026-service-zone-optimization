"""Synthetic, behavior-based tests; no real private values are stored here."""
import gzip
import io
import json
import lzma
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import tarfile
import unittest
import zipfile
import zlib

from privacy_check import Scanner


def private_home():
    return '/' + 'home/' + 'synthetic-person/'


class PrivacyChecks(unittest.TestCase):
    def test_session_links_are_blocked_without_blocking_normal_site_links(self):
        session = 'https://' + 'claude.ai/code/' + 'session_' + 'SyntheticSession123'
        checker = Scanner()
        checker.data('commit-message.txt', ('Claude-' + 'Session: ' + session).encode())
        checker.data('normal.txt', b'https://claude.ai/ friend <friend@example.test>')
        self.assertEqual(len(checker.findings), 1)
        self.assertEqual(checker.findings[0]['rule'], 'claude-session-link')
        self.assertEqual(checker.findings[0]['source'], 'commit-message.txt')

    def test_independent_private_patterns_and_public_allowance(self):
        checker = Scanner({'forbidden_literals': ['Synthetic Surname'],
                           'forbidden_regex': [r'private-mailbox@[^\s]+']})
        checker.data('evidence.txt', b'Synthetic Surname\nprivate-mailbox@example.test\n')
        checker.data('public.txt', b'public-account <public@users.noreply.github.com>\nother-author <other@example.test>\n')
        self.assertEqual(len(checker.findings), 2)
        self.assertEqual({item['source'] for item in checker.findings}, {'evidence.txt'})
        self.assertNotIn('Synthetic Surname', json.dumps(checker.result()))

    def test_homes_binary_utf16_and_placeholders(self):
        checker = Scanner()
        checker.data('object.bin', b'\x00\xff' + private_home().encode() + b'project\x00')
        checker.data('metadata.bin', (private_home() + 'notes').encode('utf-16-le'))
        checker.data('safe.txt', ('./relative/path /' + 'home/user/tool').encode())
        self.assertEqual({item['source'] for item in checker.findings}, {'object.bin', 'metadata.bin'})

    def test_private_artifact_directory_id_is_context_specific(self):
        identifier = '01234567-89ab-7cde-8f01-23456789abcd'
        checker = Scanner()
        checker.data('report.txt', ('outputs/' + identifier + '/result.xlsx').encode())
        checker.data('study.txt', ('study_id=' + identifier).encode())
        self.assertEqual(len(checker.findings), 1)
        self.assertEqual(checker.findings[0]['source'], 'report.txt')

    def test_nested_zip_member_names_and_gzip_payloads(self):
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, 'w') as archive:
            archive.writestr(private_home() + 'notes.txt', b'harmless')
            archive.writestr('binary.pyc', b'\x00' + private_home().encode())
        outer = io.BytesIO()
        with zipfile.ZipFile(outer, 'w') as archive:
            archive.writestr('inner.zip', inner.getvalue())
            archive.writestr('report.gz', gzip.compress(private_home().encode()))
        checker = Scanner()
        checker.data('submission.zip', outer.getvalue())
        locations = {item['source'] for item in checker.findings}
        self.assertIn('submission.zip!inner.zip!<member-name>', locations)
        self.assertIn('submission.zip!inner.zip!binary.pyc', locations)
        self.assertIn('submission.zip!report.gz!<gzip>', locations)

    def test_compressed_elf_debugdata(self):
        names = b'\x00.shstrtab\x00.gnu_debugdata\x00'
        packed = lzma.compress(private_home().encode())
        offset_names = 64
        offset_packed = offset_names + len(names)
        section_offset = offset_packed + len(packed)
        header = bytearray(64)
        header[:7] = b'\x7fELF\x02\x01\x01'
        struct.pack_into('<Q', header, 40, section_offset)
        struct.pack_into('<HHH', header, 58, 64, 3, 1)
        null = bytes(64)
        strings = struct.pack('<IIQQQQIIQQ', 1, 3, 0, 0, offset_names, len(names), 0, 0, 1, 0)
        debug = struct.pack('<IIQQQQIIQQ', 11, 1, 0, 0, offset_packed, len(packed), 0, 0, 1, 0)
        checker = Scanner()
        checker.data('program', bytes(header) + names + packed + null + strings + debug)
        self.assertTrue(checker.result()['complete'])
        self.assertTrue(any(item['source'] == 'program!.gnu_debugdata' for item in checker.findings))

    def test_symlink_target_is_checked_without_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            (repo / 'link').symlink_to(private_home() + 'external', target_is_directory=True)
            checker = Scanner()
            checker.worktree(repo)
            self.assertEqual(checker.checked, 1)
            self.assertEqual(checker.findings[0]['source'], 'link')

    def test_compressed_image_metadata_and_pdf_stream(self):
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'zTXt', b'Comment\0\0' + zlib.compress(private_home().encode())) + chunk(b'IEND', b'')
        checker = Scanner()
        checker.data('plot.png', png)
        pdf = b'%PDF-1.4\n<< /Filter /FlateDecode >>\nstream\n' + zlib.compress(private_home().encode()) + b'\nendstream\n'
        checker.data('report.pdf', pdf)
        self.assertTrue(any(item['source'] == 'plot.png!zTXt' for item in checker.findings))
        self.assertTrue(any(item['source'] == 'report.pdf!<PDF-Flate-0>' for item in checker.findings))

    def test_bad_archive_and_expansion_limit_fail_closed(self):
        checker = Scanner()
        checker.data('damaged.zip', b'PK\x03\x04broken')
        self.assertFalse(checker.result()['complete'])
        packed = io.BytesIO()
        with zipfile.ZipFile(packed, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('large.txt', 'x' * 5000)
        checker = Scanner(max_bytes=1000)
        checker.data('large.zip', packed.getvalue())
        self.assertFalse(checker.result()['complete'])
        checker = Scanner()
        checker.data('unsupported.7z', b'7z\xbc\xaf\x27\x1c' + bytes(30))
        self.assertFalse(checker.result()['complete'])

    def test_history_includes_deleted_file_and_old_commit_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            def git(*args, **options):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL, **options)
            git('init', '-q')
            git('config', 'user.name', 'Synthetic Person')
            git('config', 'user.email', 'synthetic@example.test')
            (repo / 'removed.txt').write_text(private_home())
            git('add', '.')
            git('commit', '-qm', 'old record')
            git('rm', '-q', 'removed.txt')
            git('config', 'user.name', 'public-account')
            git('config', 'user.email', 'public@users.noreply.github.com')
            git('commit', '-qm', 'remove')
            checker = Scanner({'forbidden_literals': ['Synthetic Person', 'synthetic@example.test']})
            checker.history(repo)
            self.assertTrue(checker.result()['complete'])
            self.assertTrue(any(item['source'].endswith(':removed.txt') for item in checker.findings))
            self.assertTrue(any(item['rule'].startswith('private-literal-') for item in checker.findings))

    def test_duplicate_blob_still_checks_all_historical_filenames(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('config', 'user.name', 'public-account')
            git('config', 'user.email', 'public@users.noreply.github.com')
            (repo / 'a.txt').write_text('identical safe content')
            (repo / 'zz-Synthetic Private Name.txt').write_text('identical safe content')
            git('add', '.')
            git('commit', '-qm', 'safe message')
            checker = Scanner({'forbidden_literals': ['Synthetic Private Name']})
            checker.history(repo)
            self.assertTrue(checker.findings)
            self.assertTrue(checker.result()['complete'])

    def test_tar_nesting_limit_cannot_report_false_clean(self):
        packed = io.BytesIO()
        with zipfile.ZipFile(packed, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('note.txt', 'Synthetic Private Name')
        raw = packed.getvalue()
        for index in range(7):
            packed = io.BytesIO()
            with tarfile.open(fileobj=packed, mode='w') as archive:
                member = tarfile.TarInfo('nested-' + str(index))
                member.size = len(raw)
                archive.addfile(member, io.BytesIO(raw))
            raw = packed.getvalue()
        checker = Scanner({'forbidden_literals': ['Synthetic Private Name']})
        checker.data('nested.tar', raw)
        self.assertFalse(checker.result()['complete'])
        self.assertFalse(checker.result()['clean'])

    def test_staged_checks_index_not_later_worktree_fix(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('config', 'user.name', 'public-account')
            git('config', 'user.email', 'public@users.noreply.github.com')
            target = repo / 'report.txt'
            target.write_text(private_home())
            git('add', 'report.txt')
            target.write_text('./safe')
            checker = Scanner()
            checker.staged(repo)
            self.assertEqual(checker.findings[0]['source'], 'index:report.txt')


if __name__ == '__main__':
    unittest.main()
