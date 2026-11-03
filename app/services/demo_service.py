from sqlalchemy.orm import Session
from app.models.document import Document
from app.services import plagiarism_service, ai_detection_service


REFERENCE_CORPUS: list[dict[str, str]] = [
    {
        "title": "Ref: Transformer Self-Attention Architecture",
        "content": (
            "The Transformer architecture dispenses entirely with recurrence and convolutions, "
            "relying instead on scaled dot-product self-attention mechanisms to model global "
            "dependencies between input and output tokens. Queries, keys, and values are projected "
            "across multiple parallel attention heads so the network jointly attends to information "
            "from distinct representation subspaces at different sequence positions. Because self-attention "
            "contains no inherent notion of token order, sinusoidal or learned positional encodings are "
            "added to input embeddings at the bottom of the encoder and decoder stacks. This parallelizable "
            "design dramatically reduces training time on modern accelerators compared with sequential "
            "gated recurrent neural networks."
        ),
    },
    {
        "title": "Ref: B-Tree Indexing in Relational Storage Engines",
        "content": (
            "Relational database management systems rely on B+Tree indexes to maintain sorted keys "
            "and support logarithmic point lookups as well as efficient sequential range scans. Internal "
            "routing nodes store separator keys aligned to fixed-size disk pages, maximizing the branching "
            "factor and keeping tree height shallow even across hundreds of millions of tuples. Leaf pages "
            "contain record pointers and are linked via doubly linked sibling pointers so range predicates "
            "traverse ordered keys without revisiting internal pages. Buffer pool managers pin frequently "
            "accessed index pages in memory while write-ahead logging guarantees crash recovery during "
            "concurrent page splits."
        ),
    },
    {
        "title": "Ref: Raft Distributed Consensus & Log Replication",
        "content": (
            "Raft decomposes distributed state machine consensus into three relatively independent "
            "subproblems: leader election, log replication, and quorum safety. Every server operates "
            "in one of three states—leader, follower, or candidate—and logical time is divided into "
            "monotonically increasing numbered terms. When followers stop receiving periodic heartbeats, "
            "randomized election timeouts prevent perpetual split votes and allow a single candidate "
            "to gather votes from a strict majority cluster quorum. Once elected, the leader appends "
            "client commands to its local log, replicates entries via AppendEntries RPCs, and commits "
            "an entry only after a majority of nodes have persisted it safely."
        ),
    },
    {
        "title": "Ref: Stochastic Gradient Descent & Adaptive Optimization",
        "content": (
            "Training deep neural networks involves minimizing high-dimensional non-convex objective "
            "functions using stochastic gradient descent over randomly sampled mini-batches. Classical "
            "momentum accelerates convergence along consistent low-curvature ravines while dampening "
            "oscillations across steep Ravine walls. Adaptive optimization algorithms such as Adam "
            "maintain exponentially decaying moving averages of both first-order gradients and "
            "second-order squared gradients, scaling learning rates individually for sparse and dense "
            "parameters. Coupled with cosine learning rate warmup and weight decay regularization, "
            "adaptive optimizers escape flat saddle regions rapidly and stabilize large-batch training."
        ),
    },
]


SAMPLE_PRESETS: list[dict] = [
    {
        "id": "original_human",
        "label": "Original Human Essay",
        "tag": "Clean Control",
        "title": "Lab Reflection: Debugging a Lock-Free Ring Buffer",
        "description": "Varied sentence cadence, expressive punctuation, and original topic — expects Clean on both detectors.",
        "content": (
            "Why did our ring buffer corrupt frames only on Friday evenings? For three days, nothing "
            "made sense. My lab partner swore the producer pointer was atomic; I suspected cache-line "
            "bouncing—or worse, a compiler reordering bug hidden behind aggressive -O3 flags! We finally "
            "strapped ThreadSanitizer onto a minimal forty-line harness (after midnight, running on cold "
            "espresso and stubbornness) and watched two worker threads collide inside the wrap-around "
            "branch. One missing memory-acquire fence! That tiny oversight taught me more about weak "
            "hardware memory models than six chapters of textbook diagrams ever could: intuition fails "
            "silently under concurrency, so deterministic stress harnesses aren't optional—they're survival gear."
        ),
    },
    {
        "id": "patchwork_plagiarism",
        "label": "Patchwork Plagiarism",
        "tag": "Multi-Source Copy",
        "title": "Student Report: Modern Deep Learning Foundations",
        "description": "Blends original framing with copied passages from two stored reference papers — highlights exact spans.",
        "content": (
            "Modern sequence modeling changed rapidly over the past decade as researchers searched for "
            "faster alternatives to recurrent networks. Specifically, the Transformer architecture dispenses "
            "entirely with recurrence and convolutions, relying instead on scaled dot-product self-attention "
            "mechanisms to model global dependencies between input and output tokens. Queries, keys, and values "
            "are projected across multiple parallel attention heads so the network jointly attends to information "
            "from distinct representation subspaces at different sequence positions.\n\n"
            "Beyond architectural choices, effective optimization remains essential when fitting large models. "
            "Adaptive optimization algorithms such as Adam maintain exponentially decaying moving averages of "
            "both first-order gradients and second-order squared gradients, scaling learning rates individually "
            "for sparse and dense parameters. Consequently, combining parallel attention layers with adaptive "
            "gradient updates enables practical large-scale training in academic labs."
        ),
    },
    {
        "id": "ai_generated",
        "label": "AI-Style Generated Text",
        "tag": "High AI Signal",
        "title": "Overview of Digital Learning Platforms",
        "description": "Uniform ~18-word sentences, repetitive transitional n-grams, and flat punctuation — triggers AI detection.",
        "content": (
            "Digital learning platforms play a crucial role in modern educational environments by supporting accessible instruction for students worldwide. "
            "Furthermore, it is important to note that digital learning platforms enable personalized learning pathways across modern educational environments. "
            "In addition, it is important to note that automated assessment tools provide consistent feedback for students and educators. "
            "Moreover, digital learning platforms play a crucial role in modern educational institutions by streamlining course management processes effectively. "
            "Furthermore, it is important to note that data analytics help educators monitor student progress across digital learning platforms. "
            "Ultimately, digital learning platforms play a crucial role in modern educational transformation by promoting consistent academic outcomes."
        ),
    },
    {
        "id": "paraphrased_overlap",
        "label": "Paraphrased Technical Summary",
        "tag": "TF-IDF vs Jaccard",
        "title": "Notes on Database B+Tree Storage Pages",
        "description": "Rewords clauses from the B-Tree reference so exact 5-word shingles drop while TF-IDF cosine stays elevated.",
        "content": (
            "Modern relational storage engines depend heavily on balanced B+Tree index structures to keep keys "
            "ordered for fast logarithmic point queries and sequential range predicates. Internal index pages "
            "pack separator keys into fixed disk blocks, increasing the branching factor so tree depth stays "
            "minimal across millions of rows. At the bottom level, leaf pages store tuple pointers alongside "
            "doubly linked sibling pointers, allowing range scans to walk sorted keys directly. Meanwhile, "
            "buffer pool caching pins hot index pages in RAM while write-ahead logging preserves durability "
            "whenever concurrent insertions trigger page splits."
        ),
    },
]


def seed_reference_corpus(db: Session, reset: bool = False) -> dict:
    if reset:
        db.query(Document).delete()
        db.commit()

    existing_titles = {row.title for row in db.query(Document.title).all()}
    added = 0

    for item in REFERENCE_CORPUS:
        if item["title"] in existing_titles:
            continue
        plag_res = plagiarism_service.check_plagiarism(item["content"], None, db)
        ai_res = ai_detection_service.detect_ai_content(item["content"], db)
        doc = Document(
            title=item["title"],
            content=item["content"],
            plagiarism_score=plag_res["overall_score"],
            ai_score=ai_res["overall_score"],
            results={"plagiarism": plag_res, "ai_detection": ai_res},
        )
        db.add(doc)
        db.commit()
        added += 1

    total = db.query(Document).count()
    return {
        "seeded": added,
        "reset": reset,
        "total_documents": total,
    }


def get_sample_presets() -> list[dict]:
    return SAMPLE_PRESETS
