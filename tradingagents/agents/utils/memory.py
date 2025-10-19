import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer  # 替代OpenAI
from pathlib import Path

class FinancialSituationMemory:
    def __init__(self, name, config=None):
        # 初始化本地嵌入模型，替代OpenAI
        # 总是拿到 memory.py 所在目录
        _MODEL_PATH = Path(__file__).resolve().parent / "all-MiniLM-L6-v2"
        print(str(_MODEL_PATH))
        self.embedding_model = SentenceTransformer(str(_MODEL_PATH))  # 轻量级通用模型
        
        # 如果需要中文优化，可以使用以下模型之一：
        # self.embedding_model = SentenceTransformer('moka-ai/m3e-base')  # 中文优化模型
        # self.embedding_model = SentenceTransformer('GanymedeNil/text2vec-large-chinese')  # 中文专用
        
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)

    def get_embedding(self, text):
        """使用sentence-transformer获取文本嵌入向量"""
        # 将文本转换为嵌入向量，并转换为列表格式
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()

    def add_situations(self, situations_and_advice):
        """添加金融情景和建议到向量数据库"""
        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """使用本地嵌入模型检索相似记忆"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],  # 将距离转换为相似度分数
                }
            )

        return matched_results

def main():
    # 创建实例 - 不再需要config参数
    matcher = FinancialSituationMemory("financial_memory")

    # 示例数据
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # 添加示例数据
    matcher.add_situations(example_data)

    # 测试查询
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        print("=== 金融情景匹配结果 ===")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n匹配结果 {i}:")
            print(f"相似度分数: {rec['similarity_score']:.4f}")
            print(f"匹配情景: {rec['matched_situation']}")
            print(f"投资建议: {rec['recommendation']}")

    except Exception as e:
        print(f"错误: {str(e)}")

    # 测试嵌入功能
    print("\n=== 嵌入功能测试 ===")
    test_text = "测试文本嵌入功能"
    test_embedding = matcher.get_embedding(test_text)
    print(f"文本: '{test_text}'")
    print(f"嵌入向量维度: {len(test_embedding)}")
    print(f"嵌入向量前10个值: {test_embedding[:10]}")
    

# 测试代码
if __name__ == "__main__":
    # 创建实例 - 不再需要config参数
    matcher = FinancialSituationMemory("financial_memory")

    # 示例数据
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # 添加示例数据
    matcher.add_situations(example_data)

    # 测试查询
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        print("=== 金融情景匹配结果 ===")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n匹配结果 {i}:")
            print(f"相似度分数: {rec['similarity_score']:.4f}")
            print(f"匹配情景: {rec['matched_situation']}")
            print(f"投资建议: {rec['recommendation']}")

    except Exception as e:
        print(f"错误: {str(e)}")

    # 测试嵌入功能
    print("\n=== 嵌入功能测试 ===")
    test_text = "测试文本嵌入功能"
    test_embedding = matcher.get_embedding(test_text)
    print(f"文本: '{test_text}'")
    print(f"嵌入向量维度: {len(test_embedding)}")
    print(f"嵌入向量前10个值: {test_embedding[:10]}")