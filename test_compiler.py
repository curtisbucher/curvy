from compiler import main, VirtualMachine


def assert_out_err(capsys, out, err):
    captured = capsys.readouterr()
    assert captured.out == out
    assert captured.err == err


def test_ops(capsys):
    vm = VirtualMachine()
    main(vm, "2 + 2")
    assert_out_err(capsys, "4\n", "")
    main(vm, "2 - 2 ** 5")
    assert_out_err(capsys, "-30\n", "")
    main(vm, "'hello %s' % 'world'")
    assert_out_err(capsys, "hello world\n", "")
    # Add the rest
