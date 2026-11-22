"""Evalúa la recuperación sobre eval/questions.jsonl: Hit@k, abstención y latencia."""

import json
import time
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.knowledge import retrieval, services


class Command(BaseCommand):
    help = "Calcula Hit@k, abstención correcta y falsas abstenciones del asistente (modo público)."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="eval/questions.jsonl")
        parser.add_argument("--sweep", action="store_true", help="Prueba varios umbrales de abstención.")
        parser.add_argument("--verbose", action="store_true", help="Muestra cada pregunta.")

    def handle(self, *args, **o):
        rows = [json.loads(line) for line in Path(o["file"]).read_text().splitlines() if line.strip()]
        index = retrieval.build_index("public")
        results, times = [], []
        for r in rows:
            t0 = time.perf_counter()
            hits = index.search(r["question"], k=services.TOP_K)
            times.append((time.perf_counter() - t0) * 1000)
            titles = []
            for h in hits:
                if h.chunk.title not in titles:
                    titles.append(h.chunk.title)
            results.append((r, hits, titles))

        ans = [x for x in results if x[0]["expected"]]
        unans = [x for x in results if not x[0]["expected"]]

        def hit_at(k):
            return sum(1 for r, _, t in ans if r["expected"] in t[:k]) / len(ans)

        self.stdout.write(
            f"Corpus: {index.n} fragmentos | {len(ans)} respondibles, {len(unans)} sin respuesta"
        )
        for k in (1, 3, 4):
            self.stdout.write(f"Hit@{k}: {hit_at(k):.0%}")
        self.stdout.write(
            f"Latencia de recuperación: mediana {sorted(times)[len(times) // 2]:.2f} ms, "
            f"máx {max(times):.2f} ms"
        )

        def at_threshold(th):
            abst_ok = sum(1 for _, h, _ in unans if not h or h[0].score < th) / len(unans)
            false_abst = sum(1 for _, h, _ in ans if not h or h[0].score < th) / len(ans)
            correct = sum(1 for r, h, t in ans if h and h[0].score >= th and t and t[0] == r["expected"])
            return abst_ok, false_abst, correct / len(ans)

        rows_out = [
            (th, *at_threshold(th))
            for th in ([1.5, 2.0, 2.5, 3.0, 3.5, 4.0] if o["sweep"] else [services.min_score()])
        ]
        self.stdout.write(
            "\nUmbral(BM25) | Abstención correcta (sin respuesta) | Falsas abstenciones"
            " | Top-1 correcto y respondido"
        )
        for th, a, f, c in rows_out:
            self.stdout.write(f"{th:<6} | {a:.0%} | {f:.0%} | {c:.0%}")

        if o["verbose"]:
            for r, hits, titles in results:
                cov = f"{hits[0].score:.2f}" if hits else "-"
                ok = "OK " if (r["expected"] and titles[:1] == [r["expected"]]) else "   "
                self.stdout.write(f"{ok} score={cov:<5} {r['question']!r} -> {titles[:2]}")
