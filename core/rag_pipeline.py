"""
RAG (Retrieval-Augmented Generation) pipeline for the Flame in Freefall application.
Orchestrates vector search, knowledge graph queries, conversation memory,
and Gemini generation to produce grounded, source-cited answers.
"""

import logging
from typing import Any, Generator, Optional

from config import SYSTEM_PROMPT, TOP_K_RESULTS
from core.gemini_client import GeminiClient
from core.knowledge_graph import KnowledgeGraph
from core.memory import ConversationMemory
from core.vectorstore import VectorStore

logger = logging.getLogger(__name__)


class RAGPipeline:
    """End-to-end retrieval-augmented generation pipeline."""

    def __init__(
        self,
        vectorstore: VectorStore,
        knowledge_graph: KnowledgeGraph,
        gemini_client: GeminiClient,
        memory: ConversationMemory,
    ):
        self.vectorstore = vectorstore
        self.knowledge_graph = knowledge_graph
        self.gemini_client = gemini_client
        self.memory = memory

    # ── Main Query ────────────────────────────────────────────────────────────

    def query(
        self,
        user_question: str,
        top_k: int = TOP_K_RESULTS,
        stream: bool = False,
    ) -> dict[str, Any]:
        """Run the query through the AI routing layer, deciding whether RAG retrieval is required."""
        # ── Layer 1: AI Query Router (Conversational & Intent Classification) ────
        routed_response = self._evaluate_query_intent(user_question)
        if routed_response is not None:
            self.memory.add_turn(user_question, routed_response["answer"], [])
            return routed_response

        # ── Layer 2: Domain RAG Pipeline (Combustion Science Retrieval) ──────────
        # Step 1 – Vector search (expand top_k for exhaustive challenge brief queries)
        is_brief_query = any(term in user_question.lower() for term in [
            "1gnufsb96", "challenge brief", "challenge_brief", "docs.google.com", "challenge document", "brief"
        ])
        effective_top_k = max(top_k, 12) if is_brief_query else top_k
        search_results = self.vectorstore.search(user_question, top_k=effective_top_k)

        if is_brief_query:
            # Guarantee that ALL chunks of challenge_brief.json are supplied for exhaustive extraction
            brief_chunks = self.vectorstore.get_documents_by_source("challenge_brief.json")
            if brief_chunks:
                seen_texts = {b["text"] for b in brief_chunks}
                other_results = [r for r in search_results if r["text"] not in seen_texts]
                search_results = brief_chunks + other_results

        # Step 2 – Knowledge graph
        kg_subgraph = self._query_knowledge_graph(user_question)
        kg_context = self.knowledge_graph.to_context_string(kg_subgraph) if kg_subgraph else ""

        # Step 3 – Combine context
        vs_context = self._format_vector_results(search_results)
        combined_context = self._combine_context(vs_context, kg_context)

        # Step 4 – Conversation memory
        memory_context = self.memory.get_recent_context(n=5)
        if memory_context:
            combined_context = f"{combined_context}\n\n{memory_context}"

        # Step 5 – Prepare user question
        prompt = user_question

        # Step 6 & 7 – Generate and return
        sources = self._extract_sources(search_results)

        if stream:
            response_gen = self.gemini_client.generate_response(
                prompt, context=combined_context, stream=True
            )
            collector = _StreamCollector(response_gen, self.memory, user_question, sources)
            return {
                "answer": collector,
                "response": collector,
                "sources": sources,
                "kg_context": kg_context,
            }
        else:
            response_text = self.gemini_client.generate_response(
                prompt, context=combined_context, stream=False
            )
            self.memory.add_turn(user_question, response_text, sources)
            return {
                "answer": response_text,
                "response": response_text,
                "sources": sources,
                "kg_context": kg_context,
            }

    def _evaluate_query_intent(self, question: str) -> Optional[dict[str, Any]]:
        """Intelligent routing layer: determines if the query requires NASA RAG retrieval."""
        import re
        q = question.strip().lower()
        q_clean = re.sub(r"[^\w\s]", "", q).strip()

        # 1. Greetings (helo, hello, hi, hey, etc.)
        greetings = {
            "hi", "helo", "hello", "hey", "hiya", "howdy", "sup", "yo", "greetings",
            "good morning", "good afternoon", "good evening", "hey there", "hello there"
        }
        if q_clean in greetings or re.match(r"^(hi|helo|hello|hey|howdy)(\s+(there|flameai|bot|assistant))?$", q_clean):
            answer = (
                "Hello! I am FlameAI, your expert assistant for microgravity combustion science and spacecraft fire safety.\n\n"
                "I can assist you with:\n"
                "• Microgravity flame behavior, sphericity, and cool flames (FLEX, FLEX-2)\n"
                "• Spacecraft fire experiments (BASS, SAFFIRE, ACME, SoFIE, SPICE)\n"
                "• Material flammability in space (Nomex, PMMA, silicone, Teflon, Kapton)\n"
                "• Fire safety and suppression guidelines for ISS, Lunar (0.16g), and Martian (0.38g) habitats\n\n"
                "What would you like to explore today?"
            )
            return {"answer": answer, "response": answer, "sources": [], "kg_context": ""}

        # 2. Capabilities & Identity
        capabilities = {
            "who are you", "what are you", "what can you do", "help", "commands",
            "what is this app", "what is this", "features", "about", "what is flame in freefall"
        }
        if q_clean in capabilities or re.match(r"^(who|what)\s+are\s+you$", q_clean) or q_clean == "help":
            answer = (
                "I am FlameAI, part of the Flame in Freefall dashboard for the NASA Space Apps Challenge 2026.\n\n"
                "Capabilities:\n"
                "• Grounded Research Retrieval: Instant insights from NASA PSI & NTRS experiments (BASS, ACME, SAFFIRE, FLEX, SoFIE, SPICE).\n"
                "• Spacecraft Material Flammability: Limiting Oxygen Index (LOI), flame spread velocity, and toxicity ratings.\n"
                "• Lunar & Martian Habitat Safety: Specific guidelines for partial gravity and exploration atmospheres (34% O2).\n"
                "• Knowledge Graph Analysis: Relates experiments, materials, and safety directives.\n\n"
                "Try asking: 'Why do flames become spherical in microgravity?' or 'What did SAFFIRE teach us about spacecraft fires?'"
            )
            return {"answer": answer, "response": answer, "sources": [], "kg_context": ""}

        # 3. Gratitude & Closings
        closings = {
            "thanks", "thank you", "thx", "bye", "goodbye", "see you", "ok", "okay",
            "cool", "great", "awesome", "perfect", "got it"
        }
        if q_clean in closings or re.match(r"^(thanks|thank you)(\s+so\s+much|\s+a\s+lot)?$", q_clean):
            answer = (
                "You are welcome! Let me know if you need any more analysis on microgravity combustion or fire safety parameters."
            )
            return {"answer": answer, "response": answer, "sources": [], "kg_context": ""}

        # Query requires deep NASA knowledge base retrieval -> proceed to RAG
        return None

    # ── Convenience Methods ───────────────────────────────────────────────────

    def get_sources(self, query: str, top_k: int = TOP_K_RESULTS) -> list[dict[str, Any]]:
        """Return relevant source documents without generating an AI response."""
        results = self.vectorstore.search(query, top_k=top_k)
        return self._extract_sources(results)

    def rank_experiments(self, criteria: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Rank experiments by relevance to the given criteria.

        Uses vector search scores as the ranking signal.
        """
        results = self.vectorstore.search(criteria, top_k=top_k)

        # Group by experiment and take the best score per experiment
        experiment_scores: dict[str, dict[str, Any]] = {}
        for r in results:
            exp_name = r["metadata"].get("experiment_name", "unknown")
            score = r.get("score", 0)
            if exp_name not in experiment_scores or score > experiment_scores[exp_name]["score"]:
                experiment_scores[exp_name] = {
                    "experiment_name": exp_name,
                    "score": score,
                    "best_chunk": r["text"][:200],
                    "source": r["metadata"].get("source", ""),
                    "category": r["metadata"].get("category", ""),
                }

        ranked = sorted(experiment_scores.values(), key=lambda x: x["score"], reverse=True)
        return ranked

    # ── Private helpers ───────────────────────────────────────────────────────

    def _query_knowledge_graph(self, question: str):
        """Try to find a relevant knowledge-graph subgraph for the question.

        Extracts candidate entity names from the question by looking for
        known graph nodes that appear (case-insensitive) in the question text.
        """
        question_lower = question.lower()
        matching_nodes: list[str] = []

        for node in self.knowledge_graph.graph.nodes:
            # Match if the node name (or a significant portion) appears in the question
            node_lower = node.lower()
            if len(node_lower) >= 3 and node_lower in question_lower:
                matching_nodes.append(node)

        if not matching_nodes:
            return None

        # Merge subgraphs for all matched nodes
        import networkx as nx

        combined = nx.DiGraph()
        for node in matching_nodes[:5]:  # limit to top 5 matches
            sg = self.knowledge_graph.query_related(node, depth=2)
            if sg:
                combined = nx.compose(combined, sg)

        return combined if combined.number_of_nodes() > 0 else None

    @staticmethod
    def get_source_url(name: str = "", source: str = "") -> str:
        """Resolve an authentic, precise deep-link URL for an experiment or dataset."""
        combined = f"{name} {source}".lower()
        if "bass" in combined:
            return "https://psi.nasa.gov/investigation/BASS"
        if "acme" in combined:
            return "https://psi.nasa.gov/investigation/ACME"
        if "saffire" in combined:
            return "https://ntrs.nasa.gov/citations/20160005234"
        if "flex" in combined:
            return "https://psi.nasa.gov/investigation/FLEX"
        if "sofie" in combined:
            return "https://psi.nasa.gov/investigation/SoFIE"
        if "spice" in combined:
            return "https://psi.nasa.gov/investigation/SPICE"
        if any(w in combined for w in ["material", "polymer", "acrylic", "nomex", "teflon", "kapton", "flammability", "nasa-std-6001", "std-6001"]):
            return "https://standards.nasa.gov/standard/nasa/nasa-std-6001"
        if any(w in combined for w in ["guideline", "safety", "protocol", "habitat"]):
            return "https://standards.nasa.gov/standard/nasa/nasa-std-6001"
        if any(w in combined for w in ["1gnufsb96", "challenge_brief", "challenge brief", "brief"]):
            return "https://docs.google.com/document/d/1gnuFsb96_K2457aZGRiJVGeAuKk-xj8Zh7okbYMtC0U/edit"
        return "Exact URL not provided in database"

    @staticmethod
    def _format_vector_results(results: list[dict[str, Any]]) -> str:
        """Format vector search results into the exact structured context format for the LLM."""
        if not results:
            return ""

        formatted_context = "## Retrieved NASA Research Chunks:\n\n"
        for doc in results:
            meta = doc.get("metadata", {})
            title = meta.get("experiment_name") or meta.get("title") or "Unknown Source"
            source_file = meta.get("source", "").replace(".json", "").replace("_", " ").title()
            if source_file and source_file.lower() not in title.lower():
                full_title = f"{title} ({source_file})"
            else:
                full_title = title

            url = meta.get("url") or RAGPipeline.get_source_url(full_title, meta.get("source", ""))
            content = doc.get("text", "").strip()

            formatted_context += f"Source Title: {full_title}\nSource URL: {url}\nContent: {content}\n\n"

        return formatted_context.strip()

    @staticmethod
    def _combine_context(vs_context: str, kg_context: str) -> str:
        """Merge vector-store and knowledge-graph context strings."""
        sections = [s for s in [vs_context, kg_context] if s]
        return "\n\n".join(sections) if sections else "No relevant context found in the database."

    @staticmethod
    def _extract_sources(results: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Pull unique source titles and URLs out of search results."""
        sources: list[dict[str, str]] = []
        seen: set[str] = set()
        for r in results:
            meta = r.get("metadata", {})
            name = meta.get("experiment_name", "NASA Combustion Record")
            source_file = meta.get("source", "").replace(".json", "").replace("_", " ").title()
            label = f"{name} ({source_file})" if source_file else name
            url = RAGPipeline.get_source_url(name, meta.get("source", ""))
            if label not in seen and name != "unknown":
                seen.add(label)
                sources.append({"title": label, "url": url})
        return sources


class _StreamCollector:
    """Iterator wrapper that captures streamed text and saves it to memory
    once the stream is exhausted."""

    def __init__(
        self,
        generator: Generator[str, None, None],
        memory: ConversationMemory,
        user_question: str,
        sources: list[Any],
    ):
        self._gen = generator
        self._memory = memory
        self._user_question = user_question
        self._sources = sources
        self._collected: list[str] = []

    def __iter__(self):
        return self

    def __next__(self) -> str:
        try:
            chunk = next(self._gen)
            self._collected.append(chunk)
            return chunk
        except StopIteration:
            full_response = "".join(self._collected)
            if full_response:
                self._memory.add_turn(self._user_question, full_response, self._sources)
            raise

    def __str__(self) -> str:
        if not self._collected:
            for _ in self:
                pass
        return "".join(self._collected)
