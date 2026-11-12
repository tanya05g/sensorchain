import hashlib


def _h(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def leaf_hash(sensor_id: str, ts: str, data_json: str) -> str:
    return _h(b"\x00" + f"{sensor_id}|{ts}|{data_json}".encode()).hex()


def _node(left: str, right: str) -> str:
    return _h(b"\x01" + bytes.fromhex(left) + bytes.fromhex(right)).hex()


def _next_level(level):
    if len(level) % 2:
        level = level + [level[-1]]
    return [_node(level[i], level[i + 1]) for i in range(0, len(level), 2)]


def build_root(leaves: list) -> str:
    if not leaves:
        raise ValueError("no leaves")
    level = list(leaves)
    while len(level) > 1:
        level = _next_level(level)
    return level[0]


def build_proof(leaves: list, index: int) -> list:
    proof, level, i = [], list(leaves), index
    while len(level) > 1:
        padded = level + [level[-1]] if len(level) % 2 else level
        sib = i ^ 1
        proof.append((padded[sib], "left" if sib < i else "right"))
        level = _next_level(level)
        i //= 2
    return proof


def apply_proof(leaf: str, proof: list) -> str:
    cur = leaf
    for sibling, side in proof:
        cur = _node(sibling, cur) if side == "left" else _node(cur, sibling)
    return cur
