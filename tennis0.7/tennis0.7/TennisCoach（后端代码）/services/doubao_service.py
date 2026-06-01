import httpx
import json
import asyncio
import logging
import random

logger = logging.getLogger(__name__)


class DoubaoService:
    def __init__(self):
        # API 配置
        self.api_key = "80aa24d9-9b78-458a-81f9-8c093d0fbffd".strip()
        self.url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions".strip()
        self.model = "ep-m-20260330202605-hpzwt"

        # 创建全局异步客户端
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(50.0, connect=10.0)
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat_with_doubao(self, user_input: str, is_analysis_report: bool = False):
        """
        调用豆包接口，返回 AI 建议文本。

        Args:
            user_input: 用户输入或分析报告
            is_analysis_report: 是否为视频分析报告（True时使用专业教练提示词）

        Returns:
            AI建议文本，失败返回None
        """
        # 根据输入类型选择系统提示词
        if is_analysis_report:
            system_prompt = """你是一位有10年经验的专业网球教练，性格热情、幽默、有耐心。你正在场边看学员录像回放。

你会收到学员动作的技术分析报告，包含：
- 动作类型（正手/反手/发球）
- 整体评级（优秀/良好/一般/较差）
- 关节角度偏差和主要问题

你的反馈分两部分，**必须有情绪和温度**：

【第1句：情绪化评价】根据评级给出真实的情感反应
- 优秀（DTW<10）：
  * "哇！这球打得太漂亮了！"
  * "牛啊！动作标准得没话说！"
  * "完美！就是这个感觉！"
  * "太棒了！简直教科书级别！"

- 良好（DTW 10-20）：
  * "不错不错！进步明显啊！"
  * "嘿，打得挺好的！"
  * "可以可以，有点意思！"
  * "不错哦，越来越像样了！"

- 一般（DTW 20-30）：
  * "嗯...还行吧，不过还能更好"
  * "这球有点勉强啊，咱们调整一下"
  * "动作有点别扭，来来来改改"
  * "emmm，感觉差点意思"

- 较差（DTW>30）：
  * "哎呀，这球打得有点乱啊"
  * "别急别急，咱从头再来"
  * "这个...咱得好好练练了"
  * "没事没事，慢慢来，先放松"

【第2句：具体建议】用口语化、生活化的语言
- 不要说"角度偏大/偏小"
- 要说动作的**感觉**和**画面感**
- 用"像...一样"的比喻
- 加上"试试"、"来"、"看"等口语词

示例：
✅ "哇！这球打得太漂亮了！手肘再放松一丢丢就完美了。"
✅ "不错不错！手臂别绷那么紧，像甩鞭子一样挥出去。"
✅ "嗯...还行吧，膝盖蹲太低了，站得自然点来。"
✅ "哎呀，手肘架太高了！放松点，想象手里端着一杯水。"
✅ "牛啊！髋部转得很到位，就差手腕再扣一点点。"
✅ "emmm，上身太僵了，深呼吸，放松肩膀试试。"

❌ "良好。手肘别太直，膝盖多弯点。" （太机械）
❌ "动作不错。右肘+12°偏大。" （照抄数据）
❌ "可以。注意调整姿势。" （太敷衍）

**重要规则**：
1. 必须有真实的情绪（惊喜/鼓励/惋惜/着急）
2. 第1句必须是感叹句（！或？）
3. 用生活化比喻，不用专业术语
4. 每次都要不一样，避免重复
5. 总长度30-40字

记住：你是真人教练，不是机器人！要让学员感受到你在**真的**看他打球，**真的**为他高兴或着急。"""
        else:
            # 实时姿态监控的提示词（保留原来的）
            system_prompt = """你是一位经验丰富的专业网球教练，擅长纠正学员的动作姿势。

要求：
1. 说话要像真实教练一样，专业、有耐心、有教育意义
2. 特别关注角度的细微变化，给出针对性建议
3. 即便是1-5度的差异，也要给出不同的表述和建议
4. 语言简练，20字以内，口语化
5. 每次回复尽量用不同的说法，避免重复
6. 多用鼓励和指导的语气
7. 不要说废话，直接给出 actionable 的建议"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 1.3  # 提高温度，增加创造性
        }

        try:
            response = await self.client.post(
                self.url,
                headers=self.headers,
                json=payload
            )

            logger.info(f"豆包 API 响应状态: {response.status_code}")

            if response.status_code != 200:
                logger.error(f"API 请求失败: {response.status_code} - {response.text}")
                return None

            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result['choices'][0]['message']['content']
            else:
                logger.error(f"API 返回结构异常: {result}")
                return None

        except httpx.TimeoutException:
            logger.error("豆包 API 超时")
            return None
        except Exception as e:
            logger.exception(f"豆包服务异常: {e}")
            return None

    async def close(self):
        """优雅关闭客户端"""
        await self.client.aclose()


# 创建单例服务实例
service = DoubaoService()


async def get_fitness_advice(joint_data: dict):
    """
    根据关节角度生成 Prompt 并获取 AI 教练建议（实时模式）
    """
    lk = joint_data.get('left_knee', 180)
    rk = joint_data.get('right_knee', 180)
    le = joint_data.get('left_elbow', 180)
    re = joint_data.get('right_elbow', 180)

    issues = []
    if lk < 90:
        issues.append("左膝弯曲过度")
    if rk < 90:
        issues.append("右膝弯曲过度")
    if le < 120:
        issues.append("左肘位置过低")
    if re < 120:
        issues.append("右肘位置过低")
    if lk > 160 and rk > 160:
        issues.append("膝盖过于伸直")

    random.seed(lk * 1000 + rk * 100 + le * 10 + re)
    extra_words = ["请注意", "建议", "记得", "尝试", "试着", "要注意", "请保持", "保持住"]
    random_word = random.choice(extra_words)

    if issues:
        issue_desc = "、".join(issues)
        prompt = (
            f"学员网球姿势问题：{issue_desc}。"
            f"当前角度：左膝{lk}°，右膝{rk}°，左肘{le}°，右肘{re}°。"
            f"请针对这个具体角度给出纠正建议，{random_word}用不一样的说法！"
        )
    else:
        prompt = (
            f"学员网球姿势：左膝{lk}°，右膝{rk}°，左肘{le}°，右肘{re}°。"
            f"姿势不错，请给予鼓励和小建议，{random_word}用不一样的说法！"
        )

    advice = await service.chat_with_doubao(prompt, is_analysis_report=False)

    if advice is None:
        return "重心过低，请注意膝盖负担！"

    return advice.strip()


async def get_video_analysis_advice(analysis_prompt: str):
    """
    根据视频分析报告获取教练建议（视频分析模式）

    Args:
        analysis_prompt: 详细的分析报告

    Returns:
        教练建议（1-2句话）
    """
    advice = await service.chat_with_doubao(analysis_prompt, is_analysis_report=True)

    if advice is None:
        return "动作需要调整，请注意关节角度！"

    return advice.strip()


async def shutdown():
    """应用退出时关闭客户端"""
    await service.close()


# 测试代码
if __name__ == "__main__":
    async def test():
        print("🚀 测试豆包服务...\n")

        # 测试1: 实时姿态监控
        print("【测试1】实时姿态监控模式")
        test_data = {
            "left_elbow": 155,
            "right_elbow": 158,
            "left_knee": 75,
            "right_knee": 82
        }
        advice1 = await get_fitness_advice(test_data)
        print(f"实时建议: {advice1}\n")

        # 测试2: 视频分析报告
        print("【测试2】视频分析报告模式")
        analysis_report = """
【动作分析报告】
动作类型: 正手
整体评级: 良好 (DTW距离: 12.3)
关注侧: 右侧

主要问题:
1. 右肘+12.3°(偏大)
2. 右肩-10.5°(偏小)
3. 右髋+8.7°(偏大)

参考标准: federer_forehand_seg2

请作为专业网球教练，用1-2句话提醒学员最关键的问题和改进方法。
"""
        advice2 = await get_video_analysis_advice(analysis_report)
        print(f"视频分析建议: {advice2}")


    asyncio.run(test())