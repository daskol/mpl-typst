from io import BytesIO

from mpl_typst.config import Config, TypstVersion, parse_typst_compiler_version

CONFIG_DICT = {
    'preamble': 'lorem ipsum',
    'typst.detached_images': True,
    'svg.preamble': 'lorem ipsum',
}

CONFIG_TOML = """\
preamble = '#let hello = ", world!"'
unknown-key = 32
"""


class TestConfig:

    def test_from_dict(self):
        config = Config.from_dict(CONFIG_DICT, prefix='typst.')
        assert config.preamble == ''
        assert config.detached_images

    def test_from_toml(self):
        buf = BytesIO(CONFIG_TOML.encode('utf-8'))
        config = Config.from_toml(buf)
        assert config.preamble == '#let hello = ", world!"'
        assert not config.detached_images


class TestTypstVersion:

    def test_parse_release_version(self):
        output = 'typst 0.14.2 (b33de9de)'
        version = parse_typst_compiler_version(output)

        assert version == TypstVersion(0, 14, 2, revision='b33de9de')
        assert version.release == (0, 14, 2)
        assert version.revision == 'b33de9de'
        assert str(version) == '0.14.2'

    def test_parse_prerelease_version(self):
        output = 'typst 0.15.0-rc.1 (c93cf32f)'
        version = parse_typst_compiler_version(output)

        assert version == TypstVersion(0, 15, 0, ('rc', 1))
        assert version.prerelease == ('rc', 1)
        assert version.revision == 'c93cf32f'
        assert str(version) == '0.15.0-rc.1'

    def test_reject_invalid_version(self):
        assert parse_typst_compiler_version('typst latest') is None
        assert parse_typst_compiler_version('typst 0.15') is None
        assert parse_typst_compiler_version('typst 01.15.0') is None

    def test_compare_prerelease_versions(self):
        rc1 = TypstVersion(0, 15, 0, ('rc', 1))
        rc2 = TypstVersion(0, 15, 0, ('rc', 2))
        release = TypstVersion(0, 15, 0)
        assert rc1 < rc2 < release
