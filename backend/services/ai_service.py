# ai_service.py
import requests
import json

class AIService:
    def __init__(self, host="http://localhost:11434"):
        self.host = host
        self.is_available = self._check_health()

    def _check_health(self):
        try:
            requests.get(f"{self.host}", timeout=0.5)
            return True
        except:
            return False

    def get_available_models(self):
        if not self.is_available: return []
        try:
            res = requests.get(f"{self.host}/api/tags")
            if res.status_code == 200:
                data = res.json()
                return [m['name'] for m in data.get('models', [])]
        except:
            pass
        return []

    def analyze_stream(self, model, data_context, user_prompt):
        """
        流式分析接口
        :param data_context: List[Dict] 核心数据摘要
        :param user_prompt: 用户的具体指令
        """
        # 1. 构建 Prompt
        system_prompt = f"""你是一个专业的建筑工程项目数据分析师。
        请根据以下 {len(data_context)} 个项目的核心数据，回答用户的问题。
        
        数据摘要:
        {json.dumps(data_context, ensure_ascii=False)}
        
        要求:
        1. 关注回款率、欠款风险和异常金额。
        2. 如果数据量较大，请总结共性问题。
        3. 回答要简练、专业，使用 Markdown 格式。
        """

        # 2. 调用 API
        payload = {
            "model": model,
            "prompt": f"{system_prompt}\n\n用户指令: {user_prompt}",
            "stream": True
        }

        try:
            with requests.post(f"{self.host}/api/generate", json=payload, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        body = json.loads(line)
                        token = body.get("response", "")
                        yield token
                        if body.get("done"):
                            break
        except Exception as e:
            yield f"\n❌ AI 分析中断: {str(e)}"