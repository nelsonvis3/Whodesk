import pytest

from apps.knowledge.text import chunk_text, stem, tokenize


def test_tokenize_normalizes_accents_stopwords_and_plurals():
    assert tokenize("¿Cómo restablezco mi CONTRASEÑA?") == tokenize("contraseñas como restablezco")[:0] + [
        t for t in tokenize("restablezco contraseña")
    ]
    assert "como" not in tokenize("cómo hago")
    assert stem("contraseña") == stem("contraseñas")
    assert stem("facturas") == stem("factura")


def test_synonyms_map_to_same_term():
    assert tokenize("clave") == tokenize("contraseña") == tokenize("password")


@pytest.mark.parametrize("n", [0, 1, 800, 1500, 5000])
def test_chunker_sizes(n):
    sentence = "Esta es una oración de ejemplo para probar el chunker. "
    text = (sentence * (n // len(sentence) + 1))[:n]
    chunks = chunk_text(text, max_chars=600)
    assert all(c.strip() for c in chunks)  # sin fragmentos vacíos
    assert all(len(c) <= 700 for c in chunks)
    if n == 0:
        assert chunks == []
    else:
        joined = " ".join(chunks)
        assert joined.startswith(text[:40]) and len(chunks) >= (1 if n <= 600 else 2)


def test_chunker_keeps_short_paragraphs_together_and_in_order():
    text = "Primero.\n\nSegundo.\n\nTercero."
    assert chunk_text(text) == ["Primero.\n\nSegundo.\n\nTercero."]
    long = "\n\n".join(f"Párrafo {i} " + "x" * 300 for i in range(4))
    chunks = chunk_text(long, max_chars=600)
    assert len(chunks) >= 2 and chunks[0].startswith("Párrafo 0")
