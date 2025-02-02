from io import BytesIO

from mpl_typst.config import Config

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
