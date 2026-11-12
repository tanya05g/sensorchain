from sensorchain import merkle


def leaves(n):
    return [merkle.leaf_hash("s", str(i), f"[{i}]") for i in range(n)]


def test_every_proof_reaches_root():
    for n in (1, 2, 3, 7, 100):
        ls = leaves(n)
        root = merkle.build_root(ls)
        for i in range(n):
            assert merkle.apply_proof(ls[i], merkle.build_proof(ls, i)) == root


def test_edit_changes_root():
    ls = leaves(10)
    root = merkle.build_root(ls)
    ls[4] = merkle.leaf_hash("s", "4", "[999]")
    assert merkle.build_root(ls) != root


def test_reorder_changes_root():
    ls = leaves(10)
    root = merkle.build_root(ls)
    ls[2], ls[3] = ls[3], ls[2]
    assert merkle.build_root(ls) != root
