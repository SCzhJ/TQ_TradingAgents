# memory.py  —— 分段存储 & 分段召回版
import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
from dashscope import TextEmbedding
from dotenv import load_dotenv

_WINDOW = 8192      # 与 _MAX_CHARS 保持一致

class FinancialSituationMemory:
    def __init__(self, name: str, config=None):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise RuntimeError("请通过环境变量 DASHSCOPE_API_KEY 提供 DashScope 密钥")
        self.model = TextEmbedding.Models.text_embedding_v3
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)

    # ---------- 工具：把长文本切成最大 _WINDOW 字符的小段 ----------
    def _chunk_text(self, text: str) -> List[str]:
        if len(text) <= _WINDOW:
            return [text]
        chunks = []
        for i in range(0, len(text), _WINDOW):
            chunks.append(text[i:i + _WINDOW])
        return chunks

    # ---------- 工具：单段文本拿 embedding ----------
    def _embed_one(self, text: str) -> List[float]:
        resp = TextEmbedding.call(model=self.model, api_key=self.api_key, input=text)
        if resp.status_code != 200:
            raise RuntimeError(f"DashScope embedding 失败: {resp}")
        return resp.output["embeddings"][0]["embedding"]

    # ---------- 对外接口：存 ----------
    def add_situations(self, situations_and_advice: List[tuple[str, str]]) -> None:
        docs, advices, ids, embeddings = [], [], [], []
        offset = self.situation_collection.count()
        for idx, (sit, rec) in enumerate(situations_and_advice):
            chunks = self._chunk_text(sit)
            for seq, chunk in enumerate(chunks):
                docs.append(chunk)
                advices.append(rec)
                ids.append(f"{offset + idx}_{seq}")          # 唯一 ID
                embeddings.append(self._embed_one(chunk))
        self.situation_collection.add(
            documents=docs,
            metadatas=[{"recommendation": rec, "chunk_of": str(i), "chunk_seq": seq}
                      for i, (_, rec) in enumerate(situations_and_advice)
                      for seq, _ in enumerate(self._chunk_text(situations_and_advice[i][0]))],
            embeddings=embeddings,
            ids=ids
        )

    # ---------- 对外接口：查 ----------
    def get_memories(self, current_situation: str, n_matches: int = 1) -> List[Dict[str, Any]]:
        query_chunks = self._chunk_text(current_situation)
        # 每段分别查 top n_matches，再把结果合并
        merged = []
        for chunk in query_chunks:
            emb = self._embed_one(chunk)
            res = self.situation_collection.query(
                query_embeddings=[emb],
                n_results=n_matches,
                include=["metadatas", "documents", "distances"]
            )
            for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
                merged.append({
                    "matched_situation": doc,
                    "recommendation": meta["recommendation"],
                    "similarity_score": 1 - dist
                })
        # 按相似度降序取前 n_matches
        merged.sort(key=lambda x: x["similarity_score"], reverse=True)
        return merged[:n_matches]

    # ---------- 对外接口：单文本 embedding（保持兼容） ----------
    def get_embedding(self, text: str) -> List[float]:
        # 若外部直接调用，仍返回首段向量（保持维度一致）
        return self._embed_one(self._chunk_text(text)[0])


# ------------------------------------------------------------------
# 以下与原版完全一致
# ------------------------------------------------------------------
def main():
    load_dotenv()
    matcher = FinancialSituationMemory("financial_memory")
    example_data = [
        ("High inflation rate with rising interest rates and declining consumer spending"*1000,
         "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration."),
        ("Tech sector showing high volatility with increasing institutional selling pressure"*1000,
         "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows."),
        ("Strong dollar affecting emerging markets with increasing forex volatility"*1000,
         "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt."),
        ("Market showing signs of sector rotation with rising yields"*1000,
         "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates."),
    ]
    matcher.add_situations(example_data)
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """*400
    recommendations = matcher.get_memories(current_situation, n_matches=2)
    print("=== 金融情景匹配结果 ===")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n匹配结果 {i}:")
        print(f"相似度分数: {rec['similarity_score']:.4f}")
        print(f"匹配情景: {rec['matched_situation'][:200]}...")
        print(f"投资建议: {rec['recommendation'][:200]}...")

    print("\n=== 嵌入功能测试 ===")
    test_text = "测试文本嵌入功能"
    test_embedding = matcher.get_embedding(test_text)
    print(f"文本: '{test_text}'")
    print(f"嵌入向量维度: {len(test_embedding)}")
    print(f"嵌入向量前10个值: {test_embedding[:10]}")


if __name__ == "__main__":
    main()