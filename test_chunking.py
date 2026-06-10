from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
OVERLAP = 200


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )
    return splitter.split_text(text)


# ── Test helpers ───────────────────────────────────────────────────────────────

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    return condition


# ── Test 1: chunks nu depasesc chunk_size ─────────────────────────────────────

def test_size_limit():
    print("Test 1: niciun chunk nu depaseste chunk_size")
    text = " ".join([f"Propozitia numarul {i} din documentul de test." for i in range(100)])
    chunks = chunk_text(text)
    all_ok = all(len(c) <= CHUNK_SIZE for c in chunks)
    check("toate chunk-urile <= 1000 chars", all_ok,
          f"max gasit: {max(len(c) for c in chunks)} chars")
    check("s-au generat chunk-uri", len(chunks) > 1, f"{len(chunks)} chunks")


# ── Test 2: nu taie in mijlocul unui cuvant ───────────────────────────────────

def test_no_mid_word_cut():
    print("\nTest 2: chunk-urile nu taie in mijlocul unui cuvant")
    text = " ".join([f"Acesta este un cuvant_lung_{i} intr-o propozitie." for i in range(80)])
    chunks = chunk_text(text)
    mid_word_cuts = [
        c for c in chunks
        if len(c) == CHUNK_SIZE and not c[-1].isspace() and c[-1] not in ".!?, \n"
    ]
    check("niciun chunk nu se termina in mijlocul unui cuvant",
          len(mid_word_cuts) == 0,
          f"{len(mid_word_cuts)} incalcari gasite")


# ── Test 3: paragrafele sunt respectate ───────────────────────────────────────

def test_paragraph_boundaries():
    print("\nTest 3: paragrafele nu sunt sparte daca incap in chunk_size")
    paragraphs = [
        "Primul paragraf este scurt.",
        "Al doilea paragraf este si el scurt.",
        "Al treilea paragraf are tot putine cuvinte.",
    ]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text)
    # Toate paragrafele incap in 1000 chars, deci ar trebui sa fie un singur chunk
    check("paragrafe scurte => 1 singur chunk", len(chunks) == 1,
          f"s-au generat {len(chunks)} chunk-uri in loc de 1")


# ── Test 4: overlap exista intre chunk-uri consecutive ────────────────────────

def test_overlap():
    print("\nTest 4: overlap-ul exista intre chunk-uri consecutive")
    text = " ".join([f"Propozitia {i}." for i in range(200)])
    chunks = chunk_text(text)
    if len(chunks) < 2:
        check("suficiente chunk-uri pentru test", False, "prea putine chunk-uri")
        return
    # Overlap = inceputul chunk[i] apare in chunk[i-1]
    overlaps_found = 0
    for i in range(1, len(chunks)):
        head = chunks[i][:50].strip()
        if head and head in chunks[i - 1]:
            overlaps_found += 1
    check("inceputul fiecarui chunk apare in chunk-ul anterior (overlap)",
          overlaps_found == len(chunks) - 1,
          f"{overlaps_found}/{len(chunks) - 1} perechi au overlap")


# ── Test 5: text gol si text foarte scurt ────────────────────────────────────

def test_edge_cases():
    print("\nTest 5: edge cases")
    check("text gol => lista goala", chunk_text("") == [])
    short = "Un text scurt."
    result = chunk_text(short)
    check("text scurt => 1 chunk exact", result == [short], f"got: {result}")


# ── Test 6: propozitii lungi (forteaza fallback pe spatii/caractere) ──────────

def test_long_sentence():
    print("\nTest 6: propozitie foarte lunga (fara punct)")
    long_sentence = "cuvant" * 300  # 1800 chars, fara separator
    chunks = chunk_text(long_sentence)
    all_within = all(len(c) <= CHUNK_SIZE for c in chunks)
    check("propozitie > chunk_size e impartita", len(chunks) > 1,
          f"{len(chunks)} chunks")
    check("toate chunk-urile <= 1000 chars chiar si pentru text fara separatori",
          all_within,
          f"max: {max(len(c) for c in chunks)}")


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Chunking test — chunk_size={CHUNK_SIZE}, overlap={OVERLAP}\n")
    test_size_limit()
    test_no_mid_word_cut()
    test_paragraph_boundaries()
    test_overlap()
    test_edge_cases()
    test_long_sentence()
    print("\nDone.")
