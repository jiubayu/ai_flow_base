from src.infrastructure.security.password_hasher import ScryptPasswordHasher


def test_hash_and_verify_roundtrip():
    hasher = ScryptPasswordHasher()
    digest, version = hasher.hash("passw0rd")
    assert version == "scrypt"
    assert digest.startswith("scrypt$")
    assert "passw0rd" not in digest
    assert hasher.verify("passw0rd", digest)


def test_verify_rejects_wrong_password():
    hasher = ScryptPasswordHasher()
    digest, _ = hasher.hash("passw0rd")
    assert not hasher.verify("wrongpass1", digest)


def test_verify_rejects_malformed_digest():
    hasher = ScryptPasswordHasher()
    assert not hasher.verify("passw0rd", "plaintext")
    assert not hasher.verify("passw0rd", "bcrypt$deadbeef$cafe")


def test_hash_uses_random_salt():
    hasher = ScryptPasswordHasher()
    assert hasher.hash("passw0rd") != hasher.hash("passw0rd")
