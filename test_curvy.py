from curvy import main, VirtualMachine


def assert_out_err(capsys, out, err):
    captured = capsys.readouterr()
    assert captured.out == out
    assert captured.err == err


vm = VirtualMachine()


def test_ops(capsys):
    ## Optimized
    # Test Add, Sub, Mult, and Order of ops
    main(vm, "1 + (2 - 3) * 4")
    assert_out_err(capsys, "-3\n", "")

    # Test Division
    main(vm, "12 / 3")
    assert_out_err(capsys, "4.0\n", "")

    main(vm, "13 // 3")
    assert_out_err(capsys, "4\n", "")

    # Test String Modulo
    main(vm, "'hello %s' % 'world'")
    assert_out_err(capsys, "hello world\n", "")

    # Test Power
    main(vm, "2**5")
    assert_out_err(capsys, "32\n", "")

    # Unoptimized
    main(vm, "2; a ** 2; a % 2")
    assert_out_err(capsys, "4\n2\n6\n1.5\n1\n9\n1\n", "")


def test_bitwise_ops(capsys):
    # Testing bitwise ops
    main(vm, "(1 << 2) + (4 >> 2)")
    assert_out_err(capsys, "5\n", "")


def test_logical_op(capsys):
    # AND
    main(vm, "8 & 15")
    assert_out_err(capsys, "8\n", "")

    # OR
    main(vm, "8 | 7")
    assert_out_err(capsys, "15\n", "")

    # XOR
    main(vm, "8 ^ 15")
    assert_out_err(capsys, "7\n", "")


def test_assignment(capsys):
    # Testing assignment
    main(vm, "a = 1;a")
    assert_out_err(capsys, "1\n", "")

    # Testing several assignment targets
    main(vm, "a = b = 1;a;b")
    assert_out_err(capsys, "1\n1\n", "")


def test_tuple(capsys):
    # Optimized
    main(vm, "(1,2,3)")
    assert_out_err(capsys, "(1, 2, 3)\n", "")

    # Unoptimized
    main(vm, "a = 1; (a,2,3)")
    assert_out_err(capsys, "(1, 2, 3)\n", "")


def test_list(capsys):
    # Optimized
    main(vm, "[1,2,3]")
    assert_out_err(capsys, "[1, 2, 3]\n", "")

    # Unoptimized
    main(vm, "a = 1; [a,2,3]")
    assert_out_err(capsys, "[1, 2, 3]\n", "")


def test_set(capsys):
    # Optimized
    main(vm, "{1,1}")
    assert_out_err(capsys, "{1}\n", "")

    # Unoptimized
    main(vm, "a = 1; {a,1}")
    assert_out_err(capsys, "{1}\n", "")


def test_dict(capsys):
    # Optimized
    main(vm, "{'Curtis':1 + 2}")
    assert_out_err(capsys, "{'Curtis': 3}\n", "")

    # Unoptimized
    main(vm, "a = 1; b = 'Curtis'; {b:a + 2}")
    assert_out_err(capsys, "{'Curtis': 3}\n", "")


def test_inplace(capsys):
    main(vm, "a = 1; a+=1; a")
    assert_out_err(capsys, "2\n", "")

    main(vm, "a = 2; a-=1; a")
    assert_out_err(capsys, "1\n", "")

    main(vm, "a = 2; a*=2; a")
    assert_out_err(capsys, "4\n", "")

    main(vm, "a = 4; a/=2; a")
    assert_out_err(capsys, "2.0\n", "")


def test_del(capsys):
    try:
        main(vm, "a = 1; del a; a")
    except KeyError:
        assert True
    else:
        assert False
