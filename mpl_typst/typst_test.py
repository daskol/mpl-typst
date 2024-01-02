from mpl_typst.typst import Array, Block, Call, Dictionary, Scalar, Writer


def test_sanity():
    block = Block()

    arr = [0.1, Scalar(1, 'pt'), '2em']
    dic = {'phase': 0, 'array': arr, 'baseline': False}
    path = Call('path', *arr, **dic)
    block.append(path)

    components = (0, 0, 0, 1)
    rgb = Call('rgb', *components)
    block.append(rgb)

    writer = Writer()
    block.to_string(writer)
    assert writer.buf.getvalue() != ''
